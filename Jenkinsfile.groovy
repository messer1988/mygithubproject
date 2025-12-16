pipeline {
    agent any

    /********************************************************************
     * 🌍 GLOBAL ENV
     ********************************************************************/
    environment {
        HELM       = "/opt/homebrew/bin/helm"
        KUBECTL    = "/opt/homebrew/bin/kubectl"

        REGISTRY   = "docker.io"
        IMAGE_REPO = "python1988/nginx-app"
        IMAGE_TAG  = "${BUILD_NUMBER}"
        LATEST_TAG = "latest"

        CHART_PATH = "helm/nginx-app"
        RELEASE    = "nginx-app"
        NAMESPACE  = "default"
    }

    /********************************************************************
     * 🧩 PARAMETERS
     ********************************************************************/
    parameters {
        choice(
                name: 'DockerImage',
                choices: ['', 'nginx-app'],
                description: 'Выбор образа приложения из DockerHub'
        )
    }

    /********************************************************************
     * ⚙️ OPTIONS
     ********************************************************************/
    options {
        timestamps()
        // ansiColor('xterm') // включишь — будет ещё красивее цветом
    }

    stages {

        /******************************************************************
         * 📦 1) CHECKOUT SOURCE
         ******************************************************************/
        stage('📦 Checkout') {
            steps {
                checkout scm
                sh """
          echo "📍 Workspace:"
          pwd

          echo "📂 Files:"
          ls -la

          echo "📦 Helm charts:"
          ls -R helm || true
        """
            }
        }

        /******************************************************************
         * 🧭 2) CLUSTER HEALTHCHECK (INFO)
         ******************************************************************/
        stage('🧭 Cluster: Healthcheck') {
            steps {
                sh """
          echo "🧱 Nodes:"
          kubectl get nodes || true

          echo "🚪 Ingress controller pods:"
          kubectl -n ingress-nginx get pods || true

          echo "🐳 Minikube status:"
          minikube status || true

          echo "📋 All pods:"
          kubectl get pods -A || true

          echo "⛵ Helm version:"
          helm version || true

          echo "🔗 Cluster info:"
          kubectl cluster-info || true
        """
            }
        }

        /******************************************************************
         * 🐳 3) DOCKER DEBUG
         ******************************************************************/
        stage('🐳 Docker: Debug') {
            steps {
                sh """
          echo "PATH=$PATH"
          which docker || echo "❌ docker not found"
          docker version || echo "❌ docker CLI not available"
        """
            }
        }

        /******************************************************************
         * 🔐 4) DOCKER LOGIN
         ******************************************************************/
        stage('🔐 Docker: Login') {
            steps {
                withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
            echo "🔑 Login to ${REGISTRY}..."
            echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin ${REGISTRY}
            echo "✅ Docker login OK"
          """
                }
            }
        }

        /******************************************************************
         * 🏗️ 5) BUILD & PUSH (MULTI-ARCH)
         ******************************************************************/
        stage('🏗️ Build & Push (multi-arch)') {
            steps {
                sh """
          echo "🧱 Init buildx builder..."
          docker buildx rm ci-builder || true
          docker buildx create --name ci-builder --driver docker-container --use
          docker buildx inspect --bootstrap

          echo "🚀 Build & push:"
          echo "   - ${IMAGE_REPO}:${IMAGE_TAG}"
          echo "   - ${IMAGE_REPO}:${LATEST_TAG}"

          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -t ${IMAGE_REPO}:${IMAGE_TAG} \
            -t ${IMAGE_REPO}:${LATEST_TAG} \
            --push .

          echo "✅ Multi-arch image pushed successfully!"
        """
            }
        }

        /******************************************************************
         * 🔢 6) AUTO VERSION BUMP + COMMIT (values.yaml)
         ******************************************************************/
        stage('🔢 Helm: Auto Version Bump & Commit') {
            steps {
                script {
                    echo "🔢 Auto update image.tag in Helm values.yaml..."

                    def valuesFile = "helm/nginx-app/values.yaml"

                    def currentTag = sh(
                            script: "grep -E '^ *tag:' ${valuesFile} | awk '{print \$2}'",
                            returnStdout: true
                    ).trim()

                    echo "📘 Current image.tag: ${currentTag}"

                    def nextTag
                    if (currentTag.isInteger()) {
                        nextTag = (currentTag.toInteger() + 1).toString()
                        echo "✅ Bump tag: ${currentTag} → ${nextTag}"
                    } else {
                        echo "⚠️ Tag '${currentTag}' is not numeric. Start with 1"
                        nextTag = "1"
                    }

                    sh """
            echo "✍️ Patch values.yaml"
            sed -i '' 's/tag: ${currentTag}/tag: ${nextTag}/' ${valuesFile}
            echo "✅ values.yaml updated"
            grep -n "tag:" ${valuesFile} || true
          """

                    withCredentials([usernamePassword(
                            credentialsId: 'UserGitPush',
                            usernameVariable: 'GIT_USER',
                            passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
              echo "📤 Commit & push changes to GitHub..."
              git config user.email "jenkins@ci.local"
              git config user.name "Jenkins CI"
              git add ${valuesFile}
              git commit -m "🔄 Auto bump image.tag to ${nextTag}" || echo "ℹ️ Nothing to commit"
              git push https://\$GIT_USER:\$GIT_TOKEN@github.com/messer1988/mygithubproject.git HEAD:main
            """
                    }

                    // Tag для Helm Deploy
                    env.IMAGE_TAG = nextTag
                    echo "✅ IMAGE_TAG for deploy is now: ${env.IMAGE_TAG}"
                }
            }
        }

        /******************************************************************
         * 🔐 7) TLS GENERATION (mkcert → secret nginx-tls)
         ******************************************************************/
        stage('🔐 TLS: mkcert → Kubernetes Secret') {
            steps {
                sh """
          echo "🔐 Generate TLS for nginx.local via mkcert..."
          mkdir -p tls

          mkcert \
            -cert-file tls/nginx.local.pem \
            -key-file  tls/nginx.local-key.pem \
            nginx.local

          echo "📦 Recreate secret nginx-tls in namespace ${NAMESPACE}..."
          kubectl -n ${NAMESPACE} delete secret nginx-tls --ignore-not-found=true
          kubectl -n ${NAMESPACE} create secret tls nginx-tls \
            --cert=tls/nginx.local.pem \
            --key=tls/nginx.local-key.pem

          echo "✅ TLS secret updated"
        """
            }
        }

        /******************************************************************
         * ⛵ 8) HELM DEPLOY
         ******************************************************************/
        stage('⛵ Helm Deploy') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                    sh """
            echo "⛵ Deploy release: ${RELEASE}"
            echo "📦 Chart: ${CHART_PATH}"
            echo "🧩 Image: ${IMAGE_REPO}:${IMAGE_TAG}"
            echo "🗂️ Namespace: ${NAMESPACE}"

            ${HELM} upgrade --install ${RELEASE} ${CHART_PATH} \
              --namespace ${NAMESPACE} \
              --create-namespace \
              --set fullnameOverride=${RELEASE} \
              --set image.repository=${IMAGE_REPO} \
              --set image.tag=${IMAGE_TAG}

            echo "✅ Helm deploy finished"
          """
                }
            }
        }

        /******************************************************************
         * ✅ 9) VERIFY ROLLOUT
         ******************************************************************/
        stage('✅ Verify Rollout') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
                    sh """
            echo "⏳ Waiting for rollout..."
            ${KUBECTL} -n ${NAMESPACE} rollout status deployment/${RELEASE} --timeout=300s

            echo "📌 Current state:"
            ${KUBECTL} -n ${NAMESPACE} get deploy,po,svc,ing -o wide
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
                        sh """
              ${HELM} status ${RELEASE} -n ${NAMESPACE} >/dev/null 2>&1 \
                && ${HELM} uninstall ${RELEASE} -n ${NAMESPACE} \
                || true
            """
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