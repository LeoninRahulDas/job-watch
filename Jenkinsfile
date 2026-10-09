
pipeline {
    agent any

    triggers {
        // Run once every hour
        cron('*/15 * * * *')
    }

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    stages {

        stage('Checkout GitHub') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    userRemoteConfigs: [[
                        url: 'git@github.com:LeoninRahulDas/job-watch.git',
                        credentialsId: 'github_id'
                    ]]
                ])
            }
        }

        stage('Validate Project Files') {
            steps {
                sh '''
                    set -eu
                    test -f main.py
                    test -f requirements.txt
                    test -f seen.json
                    echo "Project files verified."
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    set -eu

                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements.txt

                    echo "Dependencies installed."
                '''
            }
        }

        stage('Run Job Watch') {
            environment {
                TELEGRAM_BOT_TOKEN = credentials('TELEGRAM_BOT_TOKEN')
                TELEGRAM_CHAT_ID   = credentials('TELEGRAM_CHAT_ID')
                GEMINI_API_KEY     = credentials('Gemini_API_Key')
                ADZUNA_APP_ID      = credentials('Adzuna_Application_ID')
                ADZUNA_APP_KEY     = credentials('Adzuna_Application_key')
            }

            steps {
                sh '''
                    set -eu
                    .venv/bin/python main.py
                '''
            }
        }

        stage('Commit and Push seen.json') {
            steps {
                script {
                    sh '''
                        set -eu

                        git config user.name "job-watch-bot"
                        git config user.email \
                            "job-watch-bot@users.noreply.github.com"

                        git add seen.json
                    '''

                    def result = sh(
                        script: 'git diff --cached --quiet',
                        returnStatus: true
                    )

                    if (result == 1) {
                        sh 'git commit -m "update seen jobs"'

                        sshagent(credentials: ['github_id']) {
                            sh '''
                                set -eu
                                git push origin HEAD:master
                            '''
                        }

                        echo 'seen.json pushed to GitHub.'
                    } else if (result == 0) {
                        echo 'No changes to seen.json.'
                    } else {
                        error('Failed to check Git changes.')
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Job-watch completed successfully.'
        }

        failure {
            echo 'Job-watch failed. Check Console Output.'
        }

        always {
            echo 'Pipeline execution finished.'
        }
    }
}
