    # The filePath to delete
    target_file_path = "codebase/ai-powered-iam-advisor-frontend/frontend/package-lock.json"

    # Query Weaviate for objects with the specified filePath
    try:
        # Construct a GraphQL query to find the object IDs
        query = f"""
        {{
            Get {{
                CodeChunk(
                    where: {{
                        path: "filePath",
                        operator: Equal,
                        valueString: "{target_file_path}"
                    }}
                ) {{
                    _additional {{
                        id
                    }}
                }}
            }}
        }}
        """
        response = request.app.state.weaviate_client.graphql_raw_query(query)

        # Debugging: Print the raw response to verify structure
        print("Raw response:", response)

        # Access the response data correctly
        #code_chunks = response.get("data", {}).get("Get", {}).get("CodeChunk", [])
        code_chunks = response.get["CodeChunk"]

        print("Code chunks:", code_chunks)

        # Extract IDs of matching objects
        objects_to_delete = [obj["_additional"]["id"] for obj in code_chunks]


        if objects_to_delete:
            # Delete each object by its ID
            chunk_collection = request.app.state.weaviate_client.collections.get(CLASS_NAME)
            for object_id in objects_to_delete:
                chunk_collection.data.delete_by_id(object_id)
                print(f"Deleted object with I: {object_id}")
        else:
            print(f"No objects found with filePath: {target_file_path}")

    except Exception as e:
        print(f"Error during deletion: {e}")

