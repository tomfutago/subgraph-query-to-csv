import json
import requests
import pandas as pd
from jinja2 import Environment, FileSystemLoader

SUBGRAPH_API_URL_CELO = "https://api.thegraph.com/subgraphs/name/toucanprotocol/celo"
SUBGRAPH_API_URL_POLYGON = "https://api.thegraph.com/subgraphs/name/toucanprotocol/matic"

def send_query(query: str, url: str) -> json:
    r = requests.post(url, json={"query": query})
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return json.loads('{"data": "error"}')

def pull_data_to_csv(chain: str, query_type: str):
    if chain == "celo":
        subgraph_url = SUBGRAPH_API_URL_CELO
    elif chain == "polygon":
        subgraph_url = SUBGRAPH_API_URL_POLYGON
    
    env = Environment(loader=FileSystemLoader("subgraph_query_to_csv/graphql/"))
    template = env.get_template(f"{query_type}.gql")

    for i in range(1, 10000, 100):
        query = template.render(id_gte = i, id_lt = i+100)
        json_output = send_query(query=query, url=subgraph_url)
        if "error" in json_output:
            print("incorrect or no data for this query")
            break
        
        df_tmp = pd.json_normalize(json_output["data"][query_type])
        if df_tmp.empty:
            break
        if i == 1: # only once
            df = pd.concat([df_tmp])
        else:
            df = pd.concat([df, df_tmp])

    # current column names list
    column_list = df.columns.to_list()
    # convert uppercase chars, ex: tokenId -> token_id
    column_list = ["".join(["_" + char.lower() if char.isupper() else char for char in col]) for col in column_list]
    # truncate column names containing dots, ex: creator.id -> creator
    column_list = [s[:s.find(".")] if s.find(".") > 0 else s for s in column_list]
    # rename dataframe columns
    df.columns = column_list
    # save pulled data
    df.to_csv(f"output/{chain}_{query_type}.csv", index=False)

pull_data_to_csv(chain="celo", query_type="retirements")
