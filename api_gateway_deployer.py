import boto3
from botocore.exceptions import *


API_ID = "5u230e7qe5"
ENDPOINT = "http://dev.elb.aws.com"
PATH = "/test/test-depth-2/test-3/45"
HTTP_METHOD = "GET"
AUTHORIZER_ID = "z1jt4j"
STAGE_NAME = "v1"

client = boto3.client("apigateway")
resource_response = client.get_resources(
    restApiId=API_ID,
)
resources = {item["path"]: item["id"] for item in resource_response["items"]}


def create_resource(parent_id: str, path: str) -> str:
    try:
        resource_response = client.create_resource(
            restApiId=API_ID,
            parentId=parent_id,
            pathPart=get_last_path_part(path),
        )

        return resource_response["id"]

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            return resources[path]

        raise e


def get_parent_resource_id(path: str) -> str:
    paths = get_paths_by_level(path)
    parent_id = resources["/"]
    for p in paths[1:-1]:
        if p not in resources:
            resources[p] = create_resource(parent_id, p)
        parent_id = resources[p]

    return parent_id


def get_path_parts(path: str) -> list[str]:
    return [""] + [p for p in path.split("/") if p != ""]


def get_paths_by_level(path: str) -> list[str]:
    paths = get_path_parts(path)
    for i in range(1, len(paths)):
        paths[i] = paths[i - 1] + "/" + paths[i]
    paths[0] = "/"
    return paths


def get_last_path_part(path: str) -> str:
    return get_path_parts(path)[-1]


def create_resource_by_path(path: str) -> str:
    parent_resource_id = get_parent_resource_id(path)

    return create_resource(parent_resource_id, path)


resource_id = create_resource_by_path(PATH)

client.put_method(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod=HTTP_METHOD,
    authorizationType="None",
    authorizerId=AUTHORIZER_ID,
)

client.put_integration(
    restApiId=API_ID,
    resourceId=resource_id,
    httpMethod=HTTP_METHOD,
    type="HTTP_PROXY",
    integrationHttpMethod=HTTP_METHOD,
    uri=ENDPOINT + PATH,
    connectionType="INTERNET",
)
client.create_deployment(restApiId=API_ID, stageName=STAGE_NAME)
