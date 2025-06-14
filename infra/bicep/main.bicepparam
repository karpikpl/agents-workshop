// --------------------------------------------------------------------------------------------------------------
// Parameter file with many existing resources specified
// --------------------------------------------------------------------------------------------------------------
using 'main.bicep'

param publicAccessEnabled = true
param searchServiceSkuName = 'basic'

param greenSoftwareSearchIndexName = 'greensoftware-intvect'

param computeDataSearchIndexName = 'compute-intvect'

param searchSemanticConfiguration = 'default'

param searchIdentifierField = 'chunk_id'

param searchContentField = 'chunk'

param searchTitleField = 'title'

param searchEmbeddingField = 'text_vector'

param searchUseVectorQuery = true

param searchServiceSemanticRankerLevel = 'free'

param azdEnvName = readEnvironmentVariable('AZURE_ENV_NAME', '')

param location = readEnvironmentVariable('AZURE_LOCATION', '')

param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID', '')

param chatImageName = readEnvironmentVariable('SERVICE_SIMPLE_CHAT_IMAGE_NAME', '')

param chatAppExists = bool(readEnvironmentVariable('SERVICE_SIMPLE_CHAT_RESOURCE_EXISTS', 'false'))

param myIpAddress = readEnvironmentVariable('MY_IP', '')

param addRoleAssignments = bool(readEnvironmentVariable('ADD_ROLE_ASSIGNMENTS', 'true'))

param openAI_deploy_location = readEnvironmentVariable('AZURE_OPENAI_DEPLOY_LOCATION', '')

param addAppRegistration = bool(readEnvironmentVariable('ADD_APP_REGISTRATION', 'false'))

param addPrivateLinkForSearch = bool(readEnvironmentVariable('ADD_PRIVATE_LINK_FOR_SEARCH', 'true'))

param addFirewallRuleForMyIp = bool(readEnvironmentVariable('ADD_FIREWALL_RULE_FOR_MY_IP', 'true'))
