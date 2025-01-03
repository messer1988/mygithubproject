pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Cloning the repository...'
                git url: 'https://github.com/messer1988/mygithubproject.git', branch: 'main'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "Hello World"
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running tests...'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
    }
}
