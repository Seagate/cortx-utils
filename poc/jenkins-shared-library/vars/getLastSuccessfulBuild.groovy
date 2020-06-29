/**
 * Get Last successful build id from ci storage
 *
 */
def call(Map config) {
  
  // function vars
  def func = "[ Get Last Successful Build Number ]"

  echo "${func} Started"

  def version=(config != null && config.version != null && config.version != "" ) ? config.version : "centos-7.7.1908"

  def buildLocation="http://ci-storage.mero.colo.seagate.com/releases/eos/integration/${version}" \

  // Execute backup commands
  def buildDateTime=sh(script: """wget ${buildLocation} -q -O - | grep 'last_successful' | grep -oP '[0-9]{2}-[a-zA-Z]{3}-[0-9]{4} [0-9]{2}:[0-9]{2}'""", returnStdout: true)
  buildDateTime=buildDateTime.trim()
  
  def buildNumber=sh(script: """wget ${buildLocation} -q -O - | grep '${buildDateTime}' | grep -oP 'href="\\K[^"]+' | grep -v 'last_successful' """, returnStdout: true)
  buildNumber=buildNumber.replaceAll("[^\\d.]", "");

  echo "${func} Completed"
  return buildNumber 
}
