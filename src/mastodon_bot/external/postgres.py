"""Interact with a postgres db"""

import logging
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector


class Database():
    """Interact with a postgres db"""

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def match_content(self, space_name, query_embedding, match_threshold, match_count):
        """Call match_documents function to retrieve similiar embeddings using cosine"""

        conn = psycopg2.connect(host=self.host, port=self.port,
                                database=self.database, user=self.user, password=self.password)

        cursor = {}
        results = []

        try:
            # adds vector support to the connection
            register_vector(conn)

            cursor = conn.cursor()

            # cursor.execute(
            #     "SELECT * FROM public.match_documents(%s, %s, %s, %s);",
            #     (space_name, query_embedding, match_threshold, match_count)
            # )
            embedding = np.array(query_embedding)
            cursor.callproc('match_documents',
                            (space_name,
                             embedding,
                             match_threshold,
                             match_count))

            # Fetch the results
            data = cursor.fetchall()
            for row in data:
                id_, content, similarity = row

                results.append(content)

                # print(f"ID: {id_}, Content: {content}, Similarity: {similarity}")

        except psycopg2.Error as postgres_error:
            logging.error(f"Error: {postgres_error}")

        finally:
            # Close the cursor and the database connection
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return results