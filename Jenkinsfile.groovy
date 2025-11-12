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
          # гарантируем, что buildx включён
          docker buildx create --name ci-builder --use || true
          docker buildx inspect --bootstrap || true

          # соберём и запушим образы под linux/amd64 (и можно добавить arm64 при желании)
          docker buildx build \
            --platform linux/amd64 \
            -t ${IMAGE_REPO}:${IMAGE_TAG} \
            -t ${IMAGE_REPO}:${LATEST_TAG} \
            --push \
            .
        """
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
            ${KUBECTL} -n ${NAMESPACE} rollout status deployment/${RELEASE} --timeout=120s
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