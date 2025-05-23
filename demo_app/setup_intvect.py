import logging
import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    AzureOpenAIEmbeddingSkill,
    AzureOpenAIVectorizerParameters,
    AzureOpenAIVectorizer,
    FieldMapping,
    HnswAlgorithmConfiguration,
    HnswParameters,
    IndexProjectionMode,
    IndexingParameters,
    IndexingParametersConfiguration,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchIndexer,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SearchIndexerDataSourceType,
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    SearchIndexerSkillset,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    SplitSkill,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
    SearchIndexerDataUserAssignedIdentity,
)
from azure.storage.blob import BlobServiceClient
from rich.logging import RichHandler
from typing import Literal

from libraries.azd import load_azd_env


def setup_index(
    azure_credential,
    index_name,
    azure_search_endpoint,
    azure_storage_connection_string,
    azure_storage_container,
    azure_openai_embedding_endpoint,
    azure_openai_embedding_deployment,
    azure_openai_embedding_model,
    azure_openai_embeddings_dimensions,
    identity_id,
    chunking_strategy: Literal["pages", "sentences"] = "pages",
):
    index_client = SearchIndexClient(azure_search_endpoint, azure_credential)
    indexer_client = SearchIndexerClient(azure_search_endpoint, azure_credential)

    data_source_connections = indexer_client.get_data_source_connections()
    if index_name in [ds.name for ds in data_source_connections]:
        logger.info(
            f"Data source connection {index_name} already exists, not re-creating"
        )
    else:
        logger.info(f"Creating data source connection: {index_name}")
        indexer_client.create_data_source_connection(
            data_source_connection=SearchIndexerDataSourceConnection(
                name=index_name,
                type=SearchIndexerDataSourceType.AZURE_BLOB,
                connection_string=azure_storage_connection_string,
                container=SearchIndexerDataContainer(name=azure_storage_container),
                identity=SearchIndexerDataUserAssignedIdentity(
                    odata_type="#Microsoft.Azure.Search.DataUserAssignedIdentity",
                    resource_id=identity_id,
                ),
            )
        )

    index_names = [index.name for index in index_client.list_indexes()]
    if index_name in index_names:
        logger.info(f"Index {index_name} already exists, not re-creating")
    else:
        logger.info(f"Creating index: {index_name}")
        index_client.create_index(
            SearchIndex(
                name=index_name,
                fields=[
                    SearchableField(
                        name="chunk_id",
                        key=True,
                        analyzer_name="keyword",
                        sortable=True,
                    ),
                    SimpleField(
                        name="parent_id",
                        type=SearchFieldDataType.String,
                        filterable=True,
                    ),
                    SearchableField(name="title"),
                    SearchableField(name="chunk"),
                    SearchField(
                        name="text_vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        vector_search_dimensions=EMBEDDINGS_DIMENSIONS,
                        vector_search_profile_name="vp",
                        stored=True,
                        hidden=False,
                    ),
                ],
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(
                            name="algo",
                            parameters=HnswParameters(
                                metric=VectorSearchAlgorithmMetric.COSINE
                            ),
                        )
                    ],
                    vectorizers=[
                        AzureOpenAIVectorizer(
                            vectorizer_name="openai_vectorizer",
                            kind="azureOpenAI",
                            parameters=AzureOpenAIVectorizerParameters(
                                resource_url=azure_openai_embedding_endpoint,
                                auth_identity=SearchIndexerDataUserAssignedIdentity(
                                    odata_type="#Microsoft.Azure.Search.DataUserAssignedIdentity",
                                    resource_id=identity_id,
                                ),
                                deployment_name=azure_openai_embedding_deployment,
                                model_name=azure_openai_embedding_model,
                            ),
                        )
                    ],
                    profiles=[
                        VectorSearchProfile(
                            name="vp",
                            algorithm_configuration_name="algo",
                            vectorizer="openai_vectorizer",
                        )
                    ],
                ),
                semantic_search=SemanticSearch(
                    configurations=[
                        SemanticConfiguration(
                            name="default",
                            prioritized_fields=SemanticPrioritizedFields(
                                title_field=SemanticField(field_name="title"),
                                content_fields=[SemanticField(field_name="chunk")],
                            ),
                        )
                    ],
                    default_configuration_name="default",
                ),
            )
        )

    skillsets = indexer_client.get_skillsets()
    if index_name in [skillset.name for skillset in skillsets]:
        logger.info(f"Skillset {index_name} already exists, not re-creating")
    else:
        logger.info(f"Creating skillset: {index_name}")
        indexer_client.create_skillset(
            skillset=SearchIndexerSkillset(
                name=index_name,
                skills=[
                    SplitSkill(
                        text_split_mode=chunking_strategy,
                        context="/document",
                        maximum_page_length=2000,
                        page_overlap_length=(
                            500 if chunking_strategy == "pages" else None
                        ),
                        inputs=[
                            InputFieldMappingEntry(
                                name="text", source="/document/content"
                            )
                        ],
                        outputs=[
                            OutputFieldMappingEntry(
                                name="textItems", target_name=chunking_strategy
                            )
                        ],
                    ),
                    AzureOpenAIEmbeddingSkill(
                        context=f"/document/{chunking_strategy}/*",
                        resource_url=azure_openai_embedding_endpoint,
                        api_key=None,
                        auth_identity=SearchIndexerDataUserAssignedIdentity(
                            odata_type="#Microsoft.Azure.Search.DataUserAssignedIdentity",
                            resource_id=identity_id,
                        ),
                        deployment_name=azure_openai_embedding_deployment,
                        model_name=azure_openai_embedding_model,
                        dimensions=azure_openai_embeddings_dimensions,
                        inputs=[
                            InputFieldMappingEntry(
                                name="text", source=f"/document/{chunking_strategy}/*"
                            )
                        ],
                        outputs=[
                            OutputFieldMappingEntry(
                                name="embedding", target_name="text_vector"
                            )
                        ],
                    ),
                ],
                index_projection=SearchIndexerIndexProjection(
                    selectors=[
                        SearchIndexerIndexProjectionSelector(
                            target_index_name=index_name,
                            parent_key_field_name="parent_id",
                            source_context=f"/document/{chunking_strategy}/*",
                            mappings=[
                                InputFieldMappingEntry(
                                    name="chunk",
                                    source=f"/document/{chunking_strategy}/*",
                                ),
                                InputFieldMappingEntry(
                                    name="text_vector",
                                    source=f"/document/{chunking_strategy}/*/text_vector",
                                ),
                                InputFieldMappingEntry(
                                    name="title",
                                    source="/document/metadata_storage_name",
                                ),
                            ],
                        )
                    ],
                    parameters=SearchIndexerIndexProjectionsParameters(
                        projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
                    ),
                ),
            )
        )

    indexers = indexer_client.get_indexers()
    if index_name in [indexer.name for indexer in indexers]:
        logger.info(f"Indexer {index_name} already exists, not re-creating")
    else:
        indexerToCreate = SearchIndexer(
            name=index_name,
            data_source_name=index_name,
            skillset_name=index_name,
            target_index_name=index_name,
            field_mappings=[
                FieldMapping(
                    source_field_name="metadata_storage_name", target_field_name="title"
                )
            ],
            parameters=IndexingParameters(
                configuration=IndexingParametersConfiguration(
                    execution_environment="private", query_timeout=None
                )
            ),
        )
        indexer_client.create_indexer(indexer=indexerToCreate)


def upload_documents(
    azure_credential,
    indexer_name,
    azure_search_endpoint,
    azure_storage_endpoint,
    azure_storage_container,
    path: str,
):
    indexer_client = SearchIndexerClient(azure_search_endpoint, azure_credential)
    # Upload the documents in /data folder to the blob storage container
    blob_client = BlobServiceClient(
        account_url=azure_storage_endpoint,
        credential=azure_credential,
        max_single_put_size=4 * 1024 * 1024,
    )
    container_client = blob_client.get_container_client(azure_storage_container)
    if not container_client.exists():
        container_client.create_container()
    existing_blobs = [blob.name for blob in container_client.list_blobs()]

    # Open each file in /data folder
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            with open(full_path, "rb") as opened_file:
                filename = os.path.basename(full_path)
                # Check if blob already exists
                if filename in existing_blobs:
                    logger.info("Blob already exists, skipping file: %s", filename)
                else:
                    logger.info("Uploading blob for file: %s", filename)
                    blob_client = container_client.upload_blob(
                        filename, opened_file, overwrite=True
                    )

    # Start the indexer
    try:
        indexer_client.run_indexer(indexer_name)
        logger.info(
            "Indexer started. Any unindexed blobs should be indexed in a few minutes, check the Azure Portal for status."
        )
    except ResourceExistsError:
        logger.info("Indexer already running, not starting again")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger = logging.getLogger("index_setup")
    logger.setLevel(logging.INFO)

    load_azd_env()

    logger.info("Checking if we need to set up Azure AI Search index...")
    if os.environ.get("AZURE_SEARCH_REUSE_EXISTING") == "true":
        logger.info(
            "Since an existing Azure AI Search index is being used, no changes will be made to the index."
        )
        exit()
    else:
        logger.info("Setting up Azure AI Search index and integrated vectorization...")

    # Used to name index, indexer, data source and skillset
    AZURE_PATTERNS_SEARCH_INDEX = os.environ["AZURE_PATTERNS_SEARCH_INDEX"]
    AZURE_COMPUTE_SEARCH_INDEX = os.environ["AZURE_COMPUTE_SEARCH_INDEX"]
    AZURE_PATTERNS_INDEX_STORAGE_CONTAINER = os.environ[
        "AZURE_PATTERNS_INDEX_STORAGE_CONTAINER"
    ]
    AZURE_COMPUTE_INDEX_STORAGE_CONTAINER = os.environ[
        "AZURE_COMPUTE_INDEX_STORAGE_CONTAINER"
    ]

    AZURE_OPENAI_EMBEDDING_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT_FOR_INDEXING"]
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    AZURE_OPENAI_EMBEDDING_MODEL = os.environ["AZURE_OPENAI_EMBEDDING_MODEL"]
    EMBEDDINGS_DIMENSIONS = 3072
    AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
    AZURE_STORAGE_ENDPOINT = os.environ["AZURE_STORAGE_ENDPOINT"]
    AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STRING"]

    USER_ASSIGNED_IDENTITY = os.environ["USER_ASSIGNED_IDENTITY_ID"]

    logger.info("AZURE_COMPUTE_SEARCH_INDEX: %s", AZURE_COMPUTE_SEARCH_INDEX)
    logger.info("AZURE_PATTERNS_SEARCH_INDEX: %s", AZURE_PATTERNS_SEARCH_INDEX)
    logger.info("AZURE_OPENAI_EMBEDDING_ENDPOINT: %s", AZURE_OPENAI_EMBEDDING_ENDPOINT)
    logger.info(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT: %s", AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    logger.info("AZURE_OPENAI_EMBEDDING_MODEL: %s", AZURE_OPENAI_EMBEDDING_MODEL)
    logger.info("EMBEDDINGS_DIMENSIONS: %s", EMBEDDINGS_DIMENSIONS)
    logger.info("AZURE_SEARCH_ENDPOINT: %s", AZURE_SEARCH_ENDPOINT)
    logger.info("AZURE_STORAGE_ENDPOINT: %s", AZURE_STORAGE_ENDPOINT)
    logger.info("AZURE_STORAGE_CONNECTION_STRING: %s", AZURE_STORAGE_CONNECTION_STRING)
    logger.info(
        "AZURE_PATTERNS_INDEX_STORAGE_CONTAINER: %s",
        AZURE_PATTERNS_INDEX_STORAGE_CONTAINER,
    )
    logger.info(
        "AZURE_COMPUTE_INDEX_STORAGE_CONTAINER: %s",
        AZURE_COMPUTE_INDEX_STORAGE_CONTAINER,
    )
    logger.info("USER_ASSIGNED_IDENTITY: %s", USER_ASSIGNED_IDENTITY)

    azure_credential = AzureDeveloperCliCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"], process_timeout=60
    )

    setup_index(
        azure_credential,
        index_name=AZURE_PATTERNS_SEARCH_INDEX,
        azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
        azure_storage_connection_string=AZURE_STORAGE_CONNECTION_STRING,
        azure_storage_container=AZURE_PATTERNS_INDEX_STORAGE_CONTAINER,
        azure_openai_embedding_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
        azure_openai_embedding_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        azure_openai_embedding_model=AZURE_OPENAI_EMBEDDING_MODEL,
        azure_openai_embeddings_dimensions=EMBEDDINGS_DIMENSIONS,
        identity_id=USER_ASSIGNED_IDENTITY,
        chunking_strategy="pages",
    )

    upload_documents(
        azure_credential,
        indexer_name=AZURE_PATTERNS_SEARCH_INDEX,
        azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
        azure_storage_endpoint=AZURE_STORAGE_ENDPOINT,
        azure_storage_container=AZURE_PATTERNS_INDEX_STORAGE_CONTAINER,
        path="./data/catalog",
    )

    setup_index(
        azure_credential,
        index_name=AZURE_COMPUTE_SEARCH_INDEX,
        azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
        azure_storage_connection_string=AZURE_STORAGE_CONNECTION_STRING,
        azure_storage_container=AZURE_COMPUTE_INDEX_STORAGE_CONTAINER,
        azure_openai_embedding_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
        azure_openai_embedding_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        azure_openai_embedding_model=AZURE_OPENAI_EMBEDDING_MODEL,
        azure_openai_embeddings_dimensions=EMBEDDINGS_DIMENSIONS,
        identity_id=USER_ASSIGNED_IDENTITY,
        chunking_strategy="pages",
    )

    upload_documents(
        azure_credential,
        indexer_name=AZURE_COMPUTE_SEARCH_INDEX,
        azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
        azure_storage_endpoint=AZURE_STORAGE_ENDPOINT,
        azure_storage_container=AZURE_COMPUTE_INDEX_STORAGE_CONTAINER,
        path="./data/compute",
    )
