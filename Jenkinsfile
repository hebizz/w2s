pipeline {
    agent none

    stages {
        // this stage is temporary, need to change
        stage('quick-success') {
            agent {label 'amd64'}
            steps {
                sh 'cat VERSION'
                sh './tests/report.sh "9c8ce7a5-1f38-48db-ae66-88892be6c3a9" "stage(quick-success): done"'
                echo 'Done'
            }
        }
    }
    post {
        unstable {
            gerritReview labels: [Verified: -1], message: "Build is unstable, there are failed tests ${env.BUILD_URL}"
        }
    }
}
