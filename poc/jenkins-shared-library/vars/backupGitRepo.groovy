/**
 * Backup git repository
 *
 * @param  src      Source git repository that want to be backedup
 * @param  dst      Destination git repo where we want to save our source backup
 */
def call(Closure body) {

  // Evaluate the body and collect the configurations in the object
  Map config = [:]
  body.resolveStrategy = Closure.DELEGATE_FIRST
  body.delegate = config
  body()

  // Input args
  def SOURCE_REPO = config.source
  def DEST_REPO = config.dest
  
  // function vars
  def func = "[ Backup Git Repo ]"
  def temp_dir="${WORKSPACE}/source_repo_${BUILD_NUMBER}"

  // Validate input args
  assert SOURCE_REPO: "${func} The required template parameter - 'source' was not set."
  assert DEST_REPO : "${func} The required template parameter - 'dest' was not set."


  // Execute backup commands
  sh """
    mkdir -p ${temp_dir}
    git clone --mirror $SOURCE_REPO ${temp_dir}
    cd ${temp_dir}
    git push --force $DEST_REPO --all
    rm -rf ${temp_dir}
  """
  echo "${func} Completed"
}
