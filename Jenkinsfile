pipeline {
  agent any

  environment {
    HELM_RELEASE = "helm/nginx-app"
    KUBE_NAMESPACE = "default"
  }

  stages {
    stage('Build Docker Image') {
      steps {
        echo 'Сборка Docker-образа (опционально)...'
        // здесь может быть docker build / push
      }
    }

    stage('Deploy via Helm') {
      steps {
        withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
          sh """
            /opt/homebrew/bin/helm upgrade --install $HELM_RELEASE ./helm/nginx-app \
              --namespace $KUBE_NAMESPACE \
              --set image.repository=pythondevops/helm/nginx-app \
              --set image.tag=${BUILD_NUMBER}
          """
        }
      }
    }

    stage('Verify Deployment') {
      steps {
        withCredentials([file(credentialsId: 'kubeconfig-dev', variable: 'KUBECONFIG')]) {
          sh '/opt/homebrew/bin/kubectl get pods -n default'
        }
      }
    }
  }

  post {
    success {
      echo "✅ Деплой успешно выполнен!"
    }
    failure {
      echo "❌ Ошибка деплоя."
    }
  }
}