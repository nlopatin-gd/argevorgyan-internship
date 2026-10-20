#!/bin/bash

# usage: ./backup.sh [path to config file]
CONFIG="${1:-/opt/backup/backup.conf}"

if [ ! -f "$CONFIG" ]; then
  echo "Config file not found: $CONFIG"
  exit 1
fi

. "$CONFIG"

LOCK_FILE="/tmp/backup.lock"

mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

send_mail() {
  if [ -z "$EMAIL_TO" ]; then
    return
  fi
  if ! command -v mail >/dev/null 2>&1; then
    log "mail command not installed, email not sent"
    return
  fi
  echo "$2" | mail -s "$1" "$EMAIL_TO"
  if [ $? -ne 0 ]; then
    log "email could not be sent"
  fi
}

fail() {
  log "ERROR: $1"
  send_mail "BACKUP FAILED on $(hostname)" "$1"
  exit 1
}

# only one copy of the script can run at a time
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "Another backup is already running. Exiting."
  exit 1
fi

log "===== backup started ====="

if [ ! -d "$SOURCE_DIR" ]; then
  fail "Source folder does not exist: $SOURCE_DIR"
fi

if ! mkdir -p "$BACKUP_DIR"; then
  fail "Cannot create backup folder: $BACKUP_DIR"
fi

SRC_NAME=$(basename "$SOURCE_DIR")
STAMP=$(date '+%Y%m%d_%H%M%S')
ARCHIVE="$BACKUP_DIR/${SRC_NAME}_${STAMP}.tar.gz"

log "Making archive: $ARCHIVE"
if ! tar -czf "$ARCHIVE" -C "$(dirname "$SOURCE_DIR")" "$SRC_NAME" 2>>"$LOG_FILE"; then
  rm -f "$ARCHIVE"
  fail "tar could not make the archive"
fi

# check that the archive is not broken
if ! tar -tzf "$ARCHIVE" >/dev/null 2>>"$LOG_FILE"; then
  rm -f "$ARCHIVE"
  fail "archive check failed, broken file was removed"
fi

SIZE=$(du -h "$ARCHIVE" | cut -f1)
log "Archive is OK, size $SIZE"

log "Removing backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -maxdepth 1 -type f -name "${SRC_NAME}_*.tar.gz" -mtime +"$RETENTION_DAYS" -print -delete >> "$LOG_FILE" 2>&1

log "backup finished OK"
send_mail "Backup OK on $(hostname)" "Backup saved: $ARCHIVE (size $SIZE)"
exit 0
