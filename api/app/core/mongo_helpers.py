from pymongo import AsyncMongoClient


async def get_all_databases(client: AsyncMongoClient) -> list[str]:
    """
    Asynchronously retrieves the names of all databases on the MongoDB server.

    Args:
        client: An instance of AsyncMongoClient.

    Returns:
        A list of database names (strings).
    """
    try:
        database_names = await client.list_database_names()
        return database_names
    except Exception as e:
        print(f"Error getting database names: {e}")
        return []

async def get_all_collections_in_database(client: AsyncMongoClient, db_name: str) -> list[str]:
    """
    Asynchronously retrieves the names of all collections within a specific database.

    Args:
        client: An instance of AsyncMongoClient.
        db_name: The name of the database to query.

    Returns:
        A list of collection names (strings) within the specified database.
    """
    try:
        db = client[db_name]
        collection_names = await db.list_collection_names()
        return collection_names
    except Exception as e:
        print(f"Error getting collections for database '{db_name}': {e}")
        return []

async def get_all_collections_across_all_databases(client: AsyncMongoClient) -> dict[str, list[str]]:
    """
    Asynchronously retrieves all collections for all databases on the MongoDB server.

    Args:
        client: An instance of AsyncMongoClient.

    Returns:
        A dictionary where keys are database names and values are lists of collection names.
    """
    all_collections = {}
    database_names = await get_all_databases(client)

    for db_name in database_names:
        # Skip system databases if you don't need them
        collections = await get_all_collections_in_database(client, db_name)
        all_collections[db_name] = collections
    return all_collections


async def get_data_from_collection(
    client: AsyncMongoClient,
    db_name: str,
    collection_name: str,
    query: dict|None = None,
    projection: dict|None = None,
    sort_by: tuple|None = None, # Example: ("age", -1) for descending age
    skip: int = 0,
    limit: int = 0 # 0 means no limit
) -> list[dict]:
    """
    Asynchronously retrieves documents from a specified MongoDB collection.

    Args:
        client: An instance of AsyncMongoClient.
        db_name: The name of the database.
        collection_name: The name of the collection.
        query: (Optional) A dictionary specifying the query filter. Defaults to an empty dict (all documents).
        projection: (Optional) A dictionary specifying which fields to include (1) or exclude (0).
                    '_id' is included by default unless explicitly excluded.
        sort_by: (Optional) A tuple (field_name, direction). Direction is 1 for ascending, -1 for descending.
        skip: (Optional) The number of documents to skip. Useful for pagination.
        limit: (Optional) The maximum number of documents to return. 0 means no limit.

    Returns:
        A list of dictionaries, where each dictionary represents a document.
    """
    if query is None:
        query = {}
    if projection is None:
        projection = {}

    try:
        db = client[db_name]
        collection = db[collection_name]

        cursor = collection.find(query, projection)

        if sort_by:
            cursor = cursor.sort(sort_by[0], sort_by[1])
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)

        documents = await cursor.to_list(length=None) # Fetch all results
        print(f"Retrieved {len(documents)} documents from '{db_name}.{collection_name}'.")
        return documents

    except Exception as e:
        print(f"Error fetching data from '{db_name}.{collection_name}': {e}")
        return []
