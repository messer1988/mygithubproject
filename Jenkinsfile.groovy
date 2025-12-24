pipeline {
    agent any
    /********************************************************************
     * 🌍 GLOBAL ENV
     ********************************************************************/
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

    /********************************************************************
     * 🧩 PARAMETERS
     ********************************************************************/
    parameters {
        choice(name: 'DockerImage', choices: ['', 'nginx-app'], description: 'Выбор образа приложения из DockerHub')
    }
    /********************************************************************
     * ⚙️ OPTIONS
     ********************************************************************/
    options {
        ansiColor('xterm')
        timestamps()
    }

    stages {
        /******************************************************************
         * 📦 1) CHECKOUT SOURCE
         ******************************************************************/
        stage('Checkout') {
            steps {
                echo '\033[35m============ CHECKOUT SOURCE ===============\033[0m'
                checkout scm
                sh 'pwd && ls -la && ls -R helm || true'
            }
        }
        /******************************************************************
         * 🧭 2) CLUSTER HEALTHCHECK (INFO)
         ******************************************************************/
        stage('Checkout_Cluster'){
            steps {
                echo '\033[35m============ CLUSTER HEALTHCHECK (INFO) ===============\033[0m'
                sh 'kubectl get nodes' //проверка работы Control Panel
                sh 'kubectl -n ingress-nginx get pods' // проверка работы ingress
                sh 'minikube status'
                sh 'kubectl get pods -A' //Вывести статус всех Pod
                sh 'helm version'
                sh 'kubectl cluster-info'

            }
        }
        /******************************************************************
         * 🐳 3) DOCKER DEBUG
         ******************************************************************/
        stage('Debug Docker') {
            steps {
                echo '\033[35m============ DOCKER DEBUG ===============\033[0m'
                sh 'echo "PATH=$PATH"'
                sh 'which docker || echo "docker not found"'
                sh 'docker version || echo "docker CLI not available"'
            }
        }

        /******************************************************************
         * 🔐 4) DOCKER LOGIN
         ******************************************************************/
        stage('Docker Login') {
            steps {
                echo '\033[35m============ DOCKER LOGIN ===============\033[0m'
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin ${REGISTRY}
          """
                }
            }
        }
        /******************************************************************
         * 🏗️ 5) BUILD & PUSH (MULTI-ARCH)
         ******************************************************************/
        stage('Build & Push (multi-arch)') {
            steps {
                echo '\033[35m============ BUILD & PUSH (MULTI-ARCH) ===============\033[0m'
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
        /******************************************************************
         * 🔢 6) AUTO VERSION BUMP + COMMIT (values.yaml)
         ******************************************************************/
        stage('Auto Version Bump & Commit') {
            steps {
                echo '\033[35m============ AUTO VERSION BUMP + COMMIT (values.yaml) ===============\033[0m'
                script {
                    echo "🔢 Автообновление версии image.tag в Helm values.yaml..."

                    // Путь к values.yaml
                    def valuesFile = "helm/nginx-app/values.yaml"

                    // Берём строку, начинающуюся с tag:
                    def currentTag = sh(script: "grep -E '^ *tag:' ${valuesFile} | awk '{print \$2}'", returnStdout: true).trim()
                    echo "📘 Текущий image.tag: ${currentTag}"

                    // Проверка: число или нет
                    def nextTag
                    if (currentTag.isInteger()) {
                        nextTag = (currentTag.toInteger() + 1).toString()
                        echo "✅ Найден числовой тег, обновляем ${currentTag} → ${nextTag}"
                    } else {
                        echo "⚠️ Тег '${currentTag}' не является числом, начинаем нумерацию с 1"
                        nextTag = "1"
                    }

                    // Обновляем values.yaml
                    sh """
                sed -i '' 's/tag: ${currentTag}/tag: ${nextTag}/' ${valuesFile}
            """

                    // Коммитим изменения в GitHub
                    withCredentials([usernamePassword(credentialsId: 'UserGitPush', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                        sh """
                    git config user.email "jenkins@ci.local"
                    git config user.name "Jenkins CI"
                    git add ${valuesFile}
                    git commit -m "🔄 Auto bump image.tag to ${nextTag}"
                    git push https://${GIT_USER}:${GIT_TOKEN}@github.com/messer1988/mygithubproject.git HEAD:main
                """
                    }

                    // Сохраняем новую версию для Helm Deploy
                    env.IMAGE_TAG = nextTag
                }
            }
        }
        /******************************************************************
         * 🔐 7) TLS GENERATION (mkcert → secret nginx-tls)
         ******************************************************************/
        stage('Generate TLS with mkcert') {
            steps {
                echo '\033[35m============ TLS GENERATION (mkcert → secret nginx-tls) ===============\033[0m'
                sh """
          echo '🔐 Генерация TLS сертификата nginx.local через mkcert...'

          # создаём сертификаты в каталоге ./tls
          mkdir -p tls
          mkcert -cert-file tls/nginx.local.pem -key-file tls/nginx.local-key.pem nginx.local

          echo '📦 Создание TLS Secret в Kubernetes...'
          kubectl -n default delete secret nginx-tls --ignore-not-found=true
          kubectl -n default create secret tls nginx-tls \
              --cert=tls/nginx.local.pem \
              --key=tls/nginx.local-key.pem

          echo '✅ TLS сертификат и Secret обновлены.'
        """
            }
        }
        /******************************************************************
         * ⛵ 8) HELM DEPLOY
         ******************************************************************/
        stage('Helm Deploy') {
            steps {
                echo '\033[35m============ HELM DEPLOY ===============\033[0m'
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
        /******************************************************************
         * ✅ 9) VERIFY ROLLOUT
         ******************************************************************/
        stage('Verify Rollout') {
            steps {
                echo '\033[35m============ VERIFY ROLLOUT ===============\033[0m'
                withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                    sh """
            ${KUBECTL} -n ${NAMESPACE} rollout status deployment/${RELEASE} --timeout=300s
            ${KUBECTL} -n ${NAMESPACE} get deploy,po,svc -o wide
          """
                }
            }
        }
    }
    /********************************************************************
     * 🧹 POST
     ********************************************************************/
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