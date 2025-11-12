pipeline {
    agent any

    environment {
        HELM       = "/opt/homebrew/bin/helm"
        KUBECTL    = "/opt/homebrew/bin/kubectl"
        REGISTRY   = "docker.io"                           // Docker Hub
        IMAGE_REPO = "python1988/nginx-app"              // замени на свой <login>/<repo>
        IMAGE_TAG  = "${BUILD_NUMBER}"                     // тег сборки
        LATEST_TAG = "latest"
        CHART_PATH = "helm/nginx-app"
        RELEASE    = "nginx-app"
        NAMESPACE  = "default"
    }
    parameters {
        choice(name: 'DockerImage', choices: ['', 'nginx-app'], description: 'Выбор образа приложения из DockerHub')
    }
//    options {
//        ansiColor('xterm')
//        timestamps()
//    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'pwd && ls -la && ls -R helm || true'
            }
        }
        stage('Debug Docker') {
            steps {
                sh 'echo "PATH=$PATH"'
                sh 'which docker || echo "docker not found"'
                sh 'docker version || echo "docker CLI not available"'
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin ${REGISTRY}
          """
                }
            }
        }

        stage('Build & Push (multi-arch)') {
            steps {
                sh """
          echo "🧱 Инициализация buildx builder..."
          docker buildx rm ci-builder || true
          docker buildx create --name ci-builder --driver docker-container --use
          docker buildx inspect --bootstrap

          echo "🚀 Сборка multi-arch образа (linux/amd64 + linux/arm64)..."
          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t ${IMAGE_REPO}:${IMAGE_TAG} \
            -t ${IMAGE_REPO}:${LATEST_TAG} \
            --push .

          echo "✅ Multi-arch образ успешно собран и запушен!"
        """
            }
        }

        stage('Auto Version Bump & Commit') {
            steps {
                script {
                    echo "🔢 Автообновление версии image.tag в Helm values.yaml..."

                    // Определим путь к файлу values.yaml
                    def valuesFile = "helm/nginx-app/values.yaml"

                    // Читаем текущий тег
                    def currentTag = sh(script: "grep 'tag:' ${valuesFile} | awk '{print \$2}'", returnStdout: true).trim()
                    def nextTag = (currentTag.toInteger() + 1).toString()

                    // Обновляем тег в файле
                    sh """
                sed -i '' 's/tag: ${currentTag}/tag: ${nextTag}/' ${valuesFile}
                echo "✅ image.tag обновлён с ${currentTag} → ${nextTag}"
            """

                    // Коммитим и пушим изменения обратно в GitHub
                    withCredentials([usernamePassword(credentialsId: 'UserGitClone', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                        sh """
                    git config user.email "jenkins@ci.local"
                    git config user.name "Jenkins CI"
                    git add ${valuesFile}
                    git commit -m "🔄 Auto bump image.tag to ${nextTag}"
                    git push https://${GIT_USER}:${GIT_TOKEN}@github.com/messer1988/mygithubproject.git HEAD:main
                """
                    }

                    // Экспортируем новую версию в env для деплоя
                    env.IMAGE_TAG = nextTag
                }
            }
        }

        stage('Helm Deploy') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                    sh """
            ${HELM} upgrade --install ${RELEASE} ${CHART_PATH} \
              --namespace ${NAMESPACE} \
              --create-namespace \
              --set fullnameOverride=${RELEASE} \
              --set image.repository=${IMAGE_REPO} \
              --set image.tag=${IMAGE_TAG}
          """
                }
            }
        }

        stage('Verify Rollout') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                    sh """
            ${KUBECTL} -n ${NAMESPACE} rollout status deployment/${RELEASE} --timeout=300s
            ${KUBECTL} -n ${NAMESPACE} get deploy,po,svc -o wide
          """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployed ${IMAGE_REPO}:${IMAGE_TAG} to ns=${NAMESPACE}"
        }
        failure {
            echo "⚠️ Failure. Attempting cleanup (optional)."
            script {
                try {
                    withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                        sh "${HELM} status ${RELEASE} -n ${NAMESPACE} >/dev/null 2>&1 && ${HELM} uninstall ${RELEASE} -n ${NAMESPACE} || true"
                    }
                } catch (err) {
                    echo "Cleanup skipped: ${err}"
                }
            }
        }
        always {
            sh 'docker logout || true'
        }
    }
}