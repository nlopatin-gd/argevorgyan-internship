pipeline {
    agent any

    environment {
        NEXUS_MAIN   = 'host.docker.internal:5001'
        NEXUS_MR     = 'host.docker.internal:5011'
        DOCKER_MAIN_REPO = 'docker-main'
        DOCKER_MR_REPO   = 'docker-mr'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Checkstyle') {
            steps {
                sh 'mvn checkstyle:checkstyle'
                archiveArtifacts artifacts: 'target/checkstyle-result.xml', allowEmptyArchive: true
            }
        }

        stage('Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                    archiveArtifacts artifacts: 'target/surefire-reports/*.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    if (env.CHANGE_ID) {
                        env.IMAGE_NAME = "${NEXUS_MR}/${DOCKER_MR_REPO}:${SHORT_GIT_COMMIT}"
                        env.NEXUS_PUSH = "${NEXUS_MR}"
                    } else {
                        env.IMAGE_NAME = "${NEXUS_MAIN}/${DOCKER_MAIN_REPO}:${SHORT_GIT_COMMIT}"
                        env.NEXUS_PUSH = "${NEXUS_MAIN}"
                    }
                    sh "docker -H unix:///Users/argevorgyan/.rd/docker.sock build -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'nexus-docker-creds',
                    usernameVariable: 'NEXUS_USERNAME',
                    passwordVariable: 'NEXUS_PASSWORD'
                )]) {
                    sh """
                        echo "${NEXUS_PASSWORD}" | docker -H unix:///Users/argevorgyan/.rd/docker.sock login ${NEXUS_PUSH} -u "${NEXUS_USERNAME}" --password-stdin
                        docker -H unix:///Users/argevorgyan/.rd/docker.sock push ${IMAGE_NAME}
                    """
                }
            }
        }

        stage('Debug') {
            steps {
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Change ID (MR?): ${env.CHANGE_ID}"
                echo "Image will be pushed to: ${IMAGE_NAME}"
                sh 'docker -H unix:///Users/argevorgyan/.rd/docker.sock info'
            }
        }
    }

    post {
        always {
            sh 'docker -H unix:///Users/argevorgyan/.rd/docker.sock logout ${NEXUS_REGISTRY} || true'
        }
    }
}
