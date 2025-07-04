# Diff Exercise
summary of the `git diff` commands I used.  
Screenshots for each step are attached.
![exercise](ex.png)
---

## Commands Used

- `git diff 1970s..current`  
  → compare files between the two branches.
  ![.](img1.png)
- `git diff 1970s..current -- queen.txt`  
  → Compared only `queen.txt` between branches.
  ![.](img2.png)
- `git diff 09cbcc9 15db960^`  
  → Compared last commit to the one before it.
![.](img3.png)
- `git add queen.txt`  
  → Staged the change after editing Adam Lambert to my name.

- `git diff`  
  → Showed unstaged changes in `fleetwoodmac.txt`.

- `git diff --cached`  
  → Showed staged change in `queen.txt`.
![.](img4.png)
- `git diff HEAD`  
  → Showed both staged and unstaged changes since last commit.
![.](img5.png)
