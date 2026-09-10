#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import json
import logging
import os
import sys
import unittest

import pendulum
from dotenv import load_dotenv

# Load this package's test .env explicitly. A bare load_dotenv() only searches
# the CWD and its parents, so it would miss a .env nested under tests/ when
# pytest is run from the package root — and module-level setup would then crash
# at import (collection) time.
_TEST_ENV = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_TEST_ENV):
    load_dotenv(_TEST_ENV, override=True)
else:
    load_dotenv()


def _load_mcp_configuration():
    """Load the test MCP configuration file if configured and present.

    Returns an empty dict when MCP_CONFIG_FILE is unset or the file is missing,
    so importing this module (pytest collection) never fails in environments
    that don't provide it.
    """
    config_file = os.getenv("MCP_CONFIG_FILE")
    if not config_file:
        return {}
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as fh:
        return json.load(fh)


setting = {
    "region_name": os.getenv("region_name"),
    "aws_access_key_id": os.getenv("aws_access_key_id"),
    "aws_secret_access_key": os.getenv("aws_secret_access_key"),
    "transport": os.getenv("MCP_TRANSPORT", "stdio").lower(),
    "port": int(os.getenv("PORT", "8000")),
    "mcp_configuration": _load_mcp_configuration(),
    "auth_provider": os.getenv("AUTH_PROVIDER", "local").lower(),
    "local_user_file": os.getenv("LOCAL_USER_FILE"),
    "admin_username": os.getenv("ADMIN_USERNAME"),
    "admin_passowrd": os.getenv("ADMIN_PASSWORD"),
    "admin_static_token": os.getenv("ADMIN_STATIC_TOKEN"),
    "cognito_user_pool_id": os.getenv("COGNITO_USER_POOL_ID"),
    "cognito_app_client_id": os.getenv("COGNITO_APP_CLIENT_ID"),
    "cognito_app_secret": os.getenv("COGNITO_APP_SECRET"),
    "funct_bucket_name": os.getenv("FUNCT_BUCKET_NAME"),
    "funct_zip_path": os.getenv("FUNCT_ZIP_PATH"),
    "funct_extract_path": os.getenv("FUNCT_EXTRACT_PATH"),
    "functs_on_local": {
        "mcp_daemon_graphql": {
            "module_name": "mcp_protocol_plugin",
            "class_name": "MCPProtocolPlugin",
        },
        "async_execute_tool_function": {
            "module_name": "mcp_protocol_plugin",
            "class_name": "MCPProtocolPlugin",
        },
        "ai_marketing_graphql": {
            "module_name": "ai_marketing_engine",
            "class_name": "AIMarketingEngine",
        },
    },
    "endpoint_id": os.getenv("endpoint_id"),
    "part_id": os.getenv("part_id", ""),
    "execute_mode": os.getenv("execute_mode"),
    "initialize_tables": int(os.getenv("initialize_tables", "0")),
    # --- Dual-backend selection ---
    "db_backend": os.getenv("db_backend", "dynamodb"),
    # PostgreSQL connection (used only when db_backend=postgresql).
    # PG_* env vars map to the setting keys Config._initialize_db_session reads.
    "db_host": os.getenv("PG_HOST"),
    "db_port": os.getenv("PG_PORT"),
    "db_user": os.getenv("PG_USER"),
    "db_password": os.getenv("PG_PASSWORD"),
    "db_schema": os.getenv("PG_DB"),
}

sys.path.insert(0, f"{os.getenv('base_dir')}/silvaengine_utility")
sys.path.insert(1, f"{os.getenv('base_dir')}/mcp_protocol_plugin")
sys.path.insert(2, f"{os.getenv('base_dir')}/mcp_function_demo")
sys.path.insert(3, f"{os.getenv('base_dir')}/mcp_marketing_collection")
sys.path.insert(4, f"{os.getenv('base_dir')}/mcp_hubspot_connector")
sys.path.insert(5, f"{os.getenv('base_dir')}/mcp_resolvepay_connector")
sys.path.insert(6, f"{os.getenv('base_dir')}/mcp_rfq_processor")
sys.path.insert(6, f"{os.getenv('base_dir')}/shopify_app_engine")
sys.path.insert(7, f"{os.getenv('base_dir')}/app_core_engine")
sys.path.insert(8, f"{os.getenv('base_dir')}/silvaengine_dynamodb_base")
sys.path.insert(9, f"{os.getenv('base_dir')}/ai_marketing_engine")
sys.path.insert(10, f"{os.getenv('base_dir')}/ai_rfq_engine")
sys.path.insert(11, f"{os.getenv('base_dir')}/silvaengine_constants")
sys.path.insert(12, f"{os.getenv('base_dir')}/mcp_shopify_extras")
sys.path.insert(13, f"{os.getenv('base_dir')}/shopify_connector")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

from mcp_protocol_plugin import MCPProtocolPlugin
from silvaengine_utility.graphql import Graphql
from silvaengine_utility.serializer import Serializer


class MCPProtocolPluginTest(unittest.TestCase):
    def setUp(self):
        self.mcp_protocol_plugin = MCPProtocolPlugin(logger, **setting)
        endpoint_id = setting.get("endpoint_id")
        context = {
            "endpoint_id": endpoint_id,
            "setting": setting,
            "logger": logger,
        }
        self.schema = Graphql.fetch_graphql_schema(
            context,
            "mcp_daemon_graphql",
        )
        logger.info("Initiate MCPProtocolPluginTest ...")

    def tearDown(self):
        logger.info("Destory MCPProtocolPluginTest ...")

    @unittest.skip("demonstrating skipping")
    def test_graphql_ping(self):
        query = Graphql.generate_graphql_operation("ping", "Query", self.schema)
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {},
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_insert_update_mcp_function(self):
        query = Graphql.generate_graphql_operation(
            "insertUpdateMcpFunction", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "name": "test-function",
                "mcpType": "tool",
                "description": "Test function description",
                "data": {
                    "inputSchema": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                    }
                },
                "annotations": None,
                "moduleName": "test_module",
                "className": "TestClass",
                "functionName": "test_function",
                "returnType": "text",
                "updatedBy": "XYZ",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_delete_mcp_function(self):
        query = Graphql.generate_graphql_operation(
            "deleteMcpFunction", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "name": "test-function",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_function(self):
        query = Graphql.generate_graphql_operation("mcpFunction", "Query", self.schema)
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "name": "hello",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_function_list(self):
        logger.info(
            "Starting comprehensive MCP function list test with module and setting retrieval..."
        )

        # Step 1: Get all MCP functions
        logger.info("Step 1: Retrieving MCP function list...")
        function_query = Graphql.generate_graphql_operation(
            "mcpFunctionList", "Query", self.schema
        )
        logger.info(f"Function Query: {function_query}")
        function_payload = {
            "query": function_query,
            "variables": {"mcp_type": "tool"},
        }
        function_response = self.mcp_protocol_plugin.mcp_daemon_graphql(
            **function_payload
        )
        function_response = Serializer.json_loads(function_response)
        mcp_functions = function_response["data"]["mcpFunctionList"]["mcpFunctionList"]

        logger.info(f"Retrieved {len(mcp_functions)} MCP functions")

        # Step 2: Get all modules
        logger.info("Step 2: Retrieving MCP module list...")
        module_query = Graphql.generate_graphql_operation(
            "mcpModuleList", "Query", self.schema
        )
        module_payload = {
            "query": module_query,
            "variables": {},
        }
        module_response = self.mcp_protocol_plugin.mcp_daemon_graphql(**module_payload)
        module_response = Serializer.json_loads(module_response)
        mcp_modules = module_response["data"]["mcpModuleList"]["mcpModuleList"]

        logger.info(f"Retrieved {len(mcp_modules)} MCP modules")

        # Step 3: Get all settings
        logger.info("Step 3: Retrieving MCP setting list...")
        setting_query = Graphql.generate_graphql_operation(
            "mcpSettingList", "Query", self.schema
        )
        setting_payload = {
            "query": setting_query,
            "variables": {},
        }
        setting_response = self.mcp_protocol_plugin.mcp_daemon_graphql(**setting_payload)
        setting_response = Serializer.json_loads(setting_response)
        mcp_settings = setting_response["data"]["mcpSettingList"]["mcpSettingList"]

        logger.info(f"Retrieved {len(mcp_settings)} MCP settings")

        # Step 4: Organize functions by type
        tools = list(filter(lambda x: x.get("mcpType") == "tool", mcp_functions))
        resources = list(
            filter(lambda x: x.get("mcpType") == "resource", mcp_functions)
        )
        prompts = list(filter(lambda x: x.get("mcpType") == "prompt", mcp_functions))

        logger.info(
            f"Function breakdown: {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts"
        )

        # Step 5: Create mapping dictionaries for easy lookup
        modules_by_name = {module["moduleName"]: module for module in mcp_modules}
        settings_by_id = {setting["settingId"]: setting for setting in mcp_settings}

        # Step 6: Build enriched configuration with module and setting details
        enriched_modules = []
        for func in mcp_functions:
            if func.get("moduleName") and func.get("className"):
                module_name = func["moduleName"]
                class_name = func["className"]

                # Get module details
                module_details = modules_by_name.get(module_name, {})

                # Find setting ID for this class (if module has classes info)
                setting_id = None
                if module_details.get("classes"):
                    for class_info in module_details["classes"]:
                        if class_info.get("class_name") == class_name:
                            setting_id = class_info.get("setting_id")
                            break

                # Get setting details
                setting_details = (
                    settings_by_id.get(setting_id, {}) if setting_id else {}
                )

                enriched_module = {
                    "module_name": module_name,
                    "package_name": module_details.get("packageName", module_name),
                    "class_name": class_name,
                    "setting_id": setting_id,
                    "setting": setting_details.get("setting", {}),
                    "source": module_details.get("source"),
                    "functions": [],
                }

                # Add function to this module
                enriched_module["functions"].append(
                    {
                        "name": func["name"],
                        "type": func["mcpType"],
                        "function_name": func.get("functionName"),
                        "return_type": func.get("returnType"),
                        "description": func.get("description"),
                    }
                )

                enriched_modules.append(enriched_module)

        # Step 7: Build complete V2 MCP configuration
        mcp_configuration = {
            "tools": [
                dict(
                    {
                        "name": tool["name"],
                        "description": tool.get("description"),
                        "annotations": tool.get("annotations"),
                    },
                    **tool.get("data", {}),
                )
                for tool in tools
            ],
            "resources": [
                dict(
                    {
                        "name": resource["name"],
                        "description": resource.get("description"),
                        "annotations": resource.get("annotations"),
                    },
                    **resource.get("data", {}),
                )
                for resource in resources
            ],
            "prompts": [
                dict(
                    {
                        "name": prompt["name"],
                        "description": prompt.get("description"),
                        "annotations": prompt.get("annotations"),
                    },
                    **prompt.get("data", {}),
                )
                for prompt in prompts
            ],
            "module_links": [
                {
                    "type": func["mcpType"],
                    "name": func["name"],
                    "module_name": func.get("moduleName"),
                    "class_name": func.get("className"),
                    "function_name": func.get("functionName"),
                    "return_type": (
                        func.get("returnType") if func["mcpType"] == "tool" else None
                    ),
                }
                for func in mcp_functions
                if func.get("moduleName") and func.get("className")
            ],
            "modules": [
                {
                    "module_name": module["moduleName"],
                    "package_name": module["packageName"],
                    "class_name": cls["class_name"],
                    "setting": settings_by_id.get(cls.get("setting_id"), {}).get(
                        "setting", {}
                    ),
                    "source": module.get("source"),
                }
                for module in mcp_modules
                for cls in module.get("classes", [])
            ],
        }

        logger.info("=== COMPLETE MCP CONFIGURATION ===")
        logger.info(f"Tools: {len(mcp_configuration['tools'])}")
        logger.info(f"Resources: {len(mcp_configuration['resources'])}")
        logger.info(f"Prompts: {len(mcp_configuration['prompts'])}")
        logger.info(f"Module Links: {len(mcp_configuration['module_links'])}")
        logger.info(f"Modules: {len(mcp_configuration['modules'])}")

        logger.info("=== ENRICHED MODULE DETAILS ===")
        for enriched_module in enriched_modules:
            logger.info(f"Module: {enriched_module['module_name']}")
            logger.info(f"  Package: {enriched_module['package_name']}")
            logger.info(f"  Class: {enriched_module['class_name']}")
            logger.info(f"  Setting ID: {enriched_module['setting_id']}")
            logger.info(f"  Setting: {enriched_module['setting']}")
            logger.info(
                f"  Functions: {[f['name'] for f in enriched_module['functions']]}"
            )

        logger.info("=== FINAL CONFIGURATION ===")
        logger.info(mcp_configuration)

    @unittest.skip("demonstrating skipping")
    def test_graphql_insert_update_mcp_function_call(self):
        query = Graphql.generate_graphql_operation(
            "insertUpdateMcpFunctionCall", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "mcpFunctionCallUuid": "07227401236394295424",
                "name": "test-function-call",
                "mcpType": "tool",
                "arguments": {},
                # "content": [],
                # "status": "completed",
                # "notes": "test notes",
                # "timeSpent": 10,
                "updatedBy": "XYZ",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_delete_mcp_function_call(self):
        query = Graphql.generate_graphql_operation(
            "deleteMcpFunctionCall", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "mcpFunctionCallUuid": "14044677568834966000",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_function_call(self):
        query = Graphql.generate_graphql_operation(
            "mcpFunctionCall", "Query", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {"mcpFunctionCallUuid": "07227401236394295424"},
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_function_call_list(self):
        query = Graphql.generate_graphql_operation(
            "mcpFunctionCallList", "Query", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {"mcp_type": "tool"},
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_insert_update_mcp_module(self):
        query = Graphql.generate_graphql_operation(
            "insertUpdateMcpModule", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "moduleName": "test_module",
                "packageName": "test_package",
                "classes": [
                    {
                        "class_name": "TestClass",
                        "setting_id": "test_setting_123",
                    },
                    {
                        "class_name": "AnotherClass",
                        "setting_id": "test_setting_456",
                    },
                ],
                "source": "s3",
                "updatedBy": "XYZ",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_delete_mcp_module(self):
        query = Graphql.generate_graphql_operation(
            "deleteMcpModule", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "moduleName": "test_module",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_get_mcp_module(self):
        query = Graphql.generate_graphql_operation("mcpModule", "Query", self.schema)
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "moduleName": "test_module",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_module_list(self):
        query = Graphql.generate_graphql_operation(
            "mcpModuleList", "Query", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {"packageName": "test_package"},
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_insert_update_mcp_setting(self):
        query = Graphql.generate_graphql_operation(
            "insertUpdateMcpSetting", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "settingId": "58986663194401980544",
                "setting": {"api_key": "test_api_key", "timeout": 30, "enabled": True},
                "updatedBy": "XYZ",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_delete_mcp_setting(self):
        query = Graphql.generate_graphql_operation(
            "deleteMcpSetting", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "settingId": "test_setting_123",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_get_mcp_setting(self):
        query = Graphql.generate_graphql_operation("mcpSetting", "Query", self.schema)
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {
                "settingId": "58986663194401980544",
            },
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_mcp_setting_list(self):
        query = Graphql.generate_graphql_operation(
            "mcpSettingList", "Query", self.schema
        )
        logger.info(f"Query: {query}")
        payload = {
            "query": query,
            "variables": {},
        }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_load_mcp_configuration(self):
        query = Graphql.generate_graphql_operation(
            "loadMcpConfiguration", "Mutation", self.schema
        )
        logger.info(f"Query: {query}")

        # Dynamically load module and get MCP_CONFIGURATION
        # module_name = "mcp_marketing_collection"
        module_name = "mcp_shopify_extras"
        # module_name = "mcp_mypay_dispatcher"
        module_name = "mcp_resolvepay_connector"
        # module_name = "mcp_rfq_processor"
        # module_name = "mcp_gpt_rfq_processor"
        # module_name = "mcp_function_demo"
        payload = {
            "query": query,
            "variables": {
                "moduleName": module_name,
                "variables": {
                    # "google_api_key": "AIzaSyD8hKTUTxuhhFKZERlASRC60_ABvvgwcck",
                    # "keyword": "supplement, ingredient, ecommerce",
                    # "promotion_products": [
                    #     {
                    #         "handle": "classic-bag-mitts",
                    #         "quantity": "1",
                    #         "variant_id": "46949468930235",
                    #     }
                    # ],
                    # "sales_rep": "Joe X.",
                    # "sales_rep_email": "joex@xyz.com",
                },
                "updatedBy": "test_user",
            },
        }
        # module_name = "mcp_resolvepay_connector"
        # import importlib

        # module = importlib.import_module(module_name)
        # test_mcp_configuration = module.MCP_CONFIGURATION

        # payload = {
        #     "query": query,
        #     "variables": {
        #         # "mcpConfiguration": test_mcp_configuration,
        #         "moduleName": module_name,
        #         "variables": {
        #             "api_key": "6FGeehtyssGTxBFJqWeaxit0ahZlSMCN",
        #             "base_url": "https://app-sandbox.resolvepay.com/api/",
        #             "merchant_id": "newedgeaisandbox",
        #         },
        #         "updatedBy": "test_user",
        #     },
        # }
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_ai_mcp(self):
        now = pendulum.now("UTC")
        months_ago = now.subtract(months=6)
        weeks_ago = now.subtract(weeks=1)
        last_month_start = now.subtract(months=1).start_of("month")
        last_month_end = now.subtract(months=1).end_of("month")

        # payload = {"method": "tools/list", "id": "1"}
        # payload = {
        #     "method": "tools/call",
        #     "params": {"name": "hello", "arguments": {"name": "TestUser"}},
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {"name": "get_google_place_setting", "arguments": {}},
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_contact_by_email",
        #         "arguments": {"email": "test@example.com"},
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_contact_profile",
        #         "arguments": {
        #             "contact": {
        #                 "email": "mike@1119-1.com",
        #                 "first_name": "Mike",
        #                 "last_name": "Wang",
        #             },
        #             "place": {"place_uuid": "00314763469908786312"},
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_shopify_customer",
        #         "arguments": {
        #             "address": {"place_uuid": "49524331017319203859"},
        #             "contact": {
        #                 "email": "bibo.1@abc.com",
        #                 "first_name": "Bibo",
        #                 "last_name": "Wang",
        #             },
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_shopify_customer",
        #         "arguments": {
        #             "address": {"place_uuid": "40008312869235340185"},
        #             "contact": {"email": "user@example.com"},
        #         },
        #     },
        # }
        payload = {
            "method": "tools/call",
            "params": {
                "name": "get_contact_profile",
                "arguments": {
                    "contact": {
                        "first_name": "Mike",
                        "last_name": "Wang",
                        "email": "mikewang@0327.com",
                    },
                    "place": {"place_uuid": "64090421430636359387"},
                },
            },
        }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "confirm_request_and_create_quotes",
        #         "arguments": {
        #             "provider_corp_external_ids": ["PROV-607"],
        #             "segment_uuid": "50965061348842553472",
        #             "request_uuid": "62041782409344598144",
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "update_quote",
        #         "arguments": {
        #             "notes": "Ship to: 1st St., Tustin, CA 92705. Shipping: Standard.",
        #             "quote_uuid": "07585098963636044967",
        #             "request_uuid": "93789478049298105511",
        #             "shipping_amount": 123.45,
        #             "shipping_method": "Standard Shipping",
        #             "status": "in_progress",
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "update_quote_item",
        #         "arguments": {
        #             "quote_uuid": "19252687768653682562",
        #             "request_uuid": "87428140187419918365",
        #             "quote_item_uuid": "98486682803161028482",
        #             "discount_amount": 1802953.2,
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "confirm_quote_and_create_installments",
        #         "arguments": {
        #             "create_single_installment": True,
        #             "quote_uuid": "78339356424781384667",
        #             "request_uuid": "18982126893246925787",
        #             "payment_method": "bank_transfer",
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "data_collect",
        #         "arguments": {
        #             "data_collect_dataset": '{"place_uuid":"45260558808639431586","first_name":"Bibo","last_name":"Wang","email":"bibo72@outlook.com","phone":"415-123-4567","company_size":"100+","reseller_certificate":"xxx.pdf","selected_products":"CBD"}'
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "submit_rfq_request",
        #         "arguments": {
        #             "email": "ashley91@example.com",
        #             "request_title": "Repurpose Synergistic Functionalities - 100 cases",
        #             "status": "initial",
        #         },
        #     },
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_contacts",
        #         "arguments": {
        #             "limit": 200,
        #             "properties": [
        #                 "email",
        #                 "firstname",
        #                 "lastname",
        #                 "lifecyclestage",
        #                 "hs_analytics_last_activity_date",
        #                 "recent_conversion_date",
        #                 "recent_conversion_event_name",
        #                 "industry",
        #                 "annualrevenue",
        #                 "numemployees",
        #                 "hubspot_owner_id",
        #                 "country",
        #                 "lastmodifieddate",
        #                 "hs_email_last_open_date",
        #                 "hs_email_last_click_date",
        #                 "hs_lead_status",
        #                 "lead_status",
        #                 "jobtitle",
        #                 "hs_analytics_num_page_views",
        #                 "hs_analytics_num_visits",
        #                 "createdate",
        #             ],
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_contact_analytics",
        #         "arguments": {
        #             "segmentation": "engagement_level",
        #             "limit": 200,
        #             "date_range": {
        #                 "start": months_ago.to_iso8601_string(),
        #                 "end": now.to_iso8601_string(),
        #             },
        #             "include_engagement": True,
        #             "mcp_function_call_uuid": "86826586620367487104",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "analyze_campaign_performance",
        #         "arguments": {
        #             "benchmark_type": "industry",
        #             "metrics": [
        #                 "open_rate",
        #                 "click_rate",
        #                 "bounce_rate",
        #                 "conversion_rate",
        #             ],
        #             "date_range": {
        #                 "start": months_ago.to_iso8601_string(),
        #                 "end": now.to_iso8601_string(),
        #             },
        #             "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "predict_lead_scores",
        #         "arguments": {
        #             "model_type": "conversion_probability",
        #             "date_range": {
        #                 "start": weeks_ago.to_iso8601_string(),
        #                 "end": now.to_iso8601_string(),
        #             },
        #             "limit": 10,
        #             "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "analyze_sales_pipeline",
        #         "arguments": {
        #             "analysis_type": "conversion_rates",
        #             "timeframe": {
        #                 "start": weeks_ago.to_iso8601_string(),
        #                 "end": now.to_iso8601_string(),
        #             },
        #             "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "create_contact_segments",
        #         "arguments": {
        #             "segmentation_type": "behavioral",
        #             "criteria": {
        #                 "engagement_score": {"min": 5},
        #                 "lifetime_value": {"min": 1000},
        #                 "date_range": {
        #                     "start": months_ago.to_iso8601_string(),
        #                     "end": now.to_iso8601_string(),
        #                 },
        #             },
        #             "number_of_segments": 5,
        #             "limit": 500,  # Reasonable limit for testing
        #             "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "forecast_revenue",
        #         "arguments": {
        #             "forecast_period": "90_days",
        #             "confidence_level": 0.95,
        #             "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "generate_executive_report",
        #         "arguments": {
        #             "report_type": "monthly",
        #             "timeframe": {
        #                 "start": "2025-08-01",  # last_month_start.to_iso8601_string(),
        #                 "end": "2025-08-31",  # last_month_end.to_iso8601_string(),
        #             },
        #             "include_forecast": True,
        #             # "departments": ["sales", "marketing"],
        #             # "detail_level": "executive",
        #             # "mcp_function_call_uuid": "10113029329119101056",
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "place_shopify_draft_order",
        #         "arguments": {
        #             "contact": {
        #                 "email": "azrael_wang@aliyun.com",
        #             },
        #             "shipping_address": {
        #                 "address1": "123 Main St",
        #                 "address2": "",
        #                 "city": "Irvine",
        #                 "province_code": "CA",
        #                 "province": "California",
        #                 "zip": "96218",
        #                 "country": "United States",
        #                 "country_code": "US",
        #                 "company": "Idea Bosque",
        #                 "first_name": "Jeffrey",
        #                 "last_name": "Wang",
        #                 "phone": "212-456-7890",
        #             },
        #             "billing_address": {
        #                 "address1": "123 Main St",
        #                 "address2": "",
        #                 "city": "Irvine",
        #                 "province_code": "CA",
        #                 "province": "California",
        #                 "zip": "96218",
        #                 "country": "United States",
        #                 "country_code": "US",
        #                 "company": "Idea Bosque",
        #                 "first_name": "Jeffrey",
        #                 "last_name": "Wang",
        #                 "phone": "212-456-7890",
        #             },
        #         },
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "get_customer",
        #         "arguments": {"customer_id": "kV4RQoiBS"},
        #     },
        #     "id": "1",
        # }
        # payload = {
        #     "method": "tools/call",
        #     "params": {
        #         "name": "request_customer_credit_check",
        #         "arguments": {
        #             "amount_requested": 10000,
        #             "customer_id": "wZk2lxzKc",
        #             "has_purchase_history": False,
        #         },
        #     },
        #     "id": "1",
        # }

        logger.info(f"Payload: {payload}")
        response = self.mcp_protocol_plugin.mcp(**payload)
        logger.info(response)

    @unittest.skip("demonstrating skipping")
    def test_ai_mcp_daemon(self):
        self.mcp_protocol_plugin.daemon()

    @staticmethod
    def _parse_graphql_response(response):
        """Normalize mcp_daemon_graphql output to a dict.

        Depending on transport, the response may already be a dict, a wrapped
        ``{"body": "..."}``, or a JSON string.
        """
        if isinstance(response, dict):
            body = response.get("body")
            if isinstance(body, (str, bytes, bytearray)):
                return Serializer.json_loads(body)
            return response
        return Serializer.json_loads(response)

    @unittest.skip("demonstrating skipping")
    def test_graphql_process_mcp_package(self):
        """End-to-end: presign, PUT a pre-built local ZIP to S3, then call
        processMcpPackage. Hits real AWS.

        For local testing, the daemon's staging paths are redirected to
        ``tests/tmp/funct_zips/`` and ``tests/tmp/functs/`` so the package is
        installed under the test tree and available for inspection or
        in-process tool tests without touching the global FUNCT_EXTRACT_PATH.
        """
        import requests

        from mcp_protocol_plugin.handlers.config import Config

        package_name = "mcp_resolvepay_connector"
        module_name = "mcp_resolvepay_connector"

        # Local install target: tests/tmp/{funct_zips,functs}/
        tmp_root = os.path.join(os.path.dirname(__file__), "tmp")
        local_zip_path = os.path.join(tmp_root, "funct_zips")
        local_extract_path = os.path.join(tmp_root, "functs")
        os.makedirs(local_zip_path, exist_ok=True)
        os.makedirs(local_extract_path, exist_ok=True)

        # Override daemon staging paths for the duration of this test.
        original_zip_path = Config.funct_zip_path
        original_extract_path = Config.funct_extract_path
        Config.funct_zip_path = local_zip_path
        Config.funct_extract_path = local_extract_path
        logger.info(
            f"Redirected staging: zip={local_zip_path}, extract={local_extract_path}"
        )

        try:
            zip_path = os.getenv("MCP_TEST_PACKAGE_ZIP") or os.path.join(
                os.getenv("base_dir"), f"{package_name}.zip"
            )
            self.assertTrue(
                os.path.isfile(zip_path),
                f"Test ZIP not found at {zip_path}. Set MCP_TEST_PACKAGE_ZIP "
                f"or place the ZIP at the default location.",
            )

            with open(zip_path, "rb") as f:
                zip_bytes = f.read()
            logger.info(f"Loaded ZIP from {zip_path}: {len(zip_bytes)} bytes")

            # 1) generateMcpPackageUploadUrl
            presign_q = Graphql.generate_graphql_operation(
                "generateMcpPackageUploadUrl", "Mutation", self.schema
            )
            presign_raw = self.mcp_protocol_plugin.mcp_daemon_graphql(
                query=presign_q, variables={"packageName": package_name}
            )
            presign = self._parse_graphql_response(presign_raw)["data"][
                "generateMcpPackageUploadUrl"
            ]
            self.assertTrue(presign["ok"], presign)
            upload_url = presign["uploadUrl"]
            s3_key = presign["s3Key"]
            logger.info(f"Presign: s3Key={s3_key}, expiresAt={presign['expiresAt']}")

            # 2) PUT to S3 (Content-Type MUST match what was presigned)
            put = requests.put(
                upload_url,
                data=zip_bytes,
                headers={"Content-Type": "application/zip"},
            )
            self.assertEqual(put.status_code, 200, f"{put.status_code} {put.text}")
            logger.info(f"S3 PUT OK: {put.status_code}")

            # 3) processMcpPackage
            process_q = Graphql.generate_graphql_operation(
                "processMcpPackage", "Mutation", self.schema
            )
            process_raw = self.mcp_protocol_plugin.mcp_daemon_graphql(
                query=process_q,
                variables={
                    "s3Key": s3_key,
                    "moduleName": module_name,
                    "packageName": package_name,
                    "source": "s3",
                    "variables": {
                        "api_key": "6FGeehtyssGTxBFJqWeaxit0ahZlSMCN",
                        "base_url": "https://app-sandbox.resolvepay.com/api/",
                        "merchant_id": "newedgeaisandbox",
                    },
                    "updatedBy": "test_user",
                },
            )
            logger.info(process_raw)
            process = self._parse_graphql_response(process_raw)["data"][
                "processMcpPackage"
            ]
            self.assertTrue(process["ok"], process)
            self.assertIsNotNone(process.get("stats"))

            # Verify the package was installed locally.
            installed_zip = os.path.join(local_zip_path, f"{package_name}.zip")
            installed_module = os.path.join(local_extract_path, module_name)
            self.assertTrue(
                os.path.isfile(installed_zip),
                f"Staged ZIP not found at {installed_zip}",
            )
            self.assertTrue(
                os.path.isdir(installed_module),
                f"Extracted module not found at {installed_module}",
            )
            logger.info(f"Installed package at {installed_module}")
        finally:
            Config.funct_zip_path = original_zip_path
            Config.funct_extract_path = original_extract_path

    @unittest.skip("demonstrating skipping")
    def test_graphql_process_mcp_package_invalid_name(self):
        """Negative path: invalid package name must be rejected before any
        S3 or DB activity."""
        query = Graphql.generate_graphql_operation(
            "processMcpPackage", "Mutation", self.schema
        )
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(
            query=query,
            variables={
                "s3Key": "bad/name.zip",
                "moduleName": "bad/name",
                "packageName": "bad/name",
                "updatedBy": "test_user",
            },
        )
        logger.info(response)
        parsed = self._parse_graphql_response(response)["data"]["processMcpPackage"]
        self.assertFalse(parsed["ok"])
        self.assertIn("Invalid package name", parsed["message"])

    @unittest.skip("demonstrating skipping")
    def test_graphql_sync_external_mcp_server(self):
        """Register a remote HTTP MCP server for proxy.

        Connects to the URL in MCP_TEST_EXTERNAL_BASE_URL, lists its
        tools/resources/prompts via MCPHttpClient, persists rows with
        source="external" and className="ExternalMCPProxy", and warms the
        partition cache. Subsequent agent tool calls dispatch through
        ExternalMCPProxy.

        Required env:
            MCP_TEST_EXTERNAL_BASE_URL   - the remote MCP JSON-RPC endpoint
        Optional env:
            MCP_TEST_EXTERNAL_SERVER_NAME - default "test_external"
            MCP_TEST_EXTERNAL_BEARER      - bearer token
            MCP_TEST_EXTERNAL_NAME_PREFIX - local-name prefix to avoid collisions
        """
        base_url = os.getenv("MCP_TEST_EXTERNAL_BASE_URL")
        if not base_url:
            self.skipTest(
                "Set MCP_TEST_EXTERNAL_BASE_URL to point at a reachable MCP "
                "HTTP server (e.g. http://localhost:8000/mcp) to run this test."
            )

        server_name = os.getenv("MCP_TEST_EXTERNAL_SERVER_NAME", "test_external")
        bearer_token = os.getenv("MCP_TEST_EXTERNAL_BEARER")
        name_prefix = os.getenv("MCP_TEST_EXTERNAL_NAME_PREFIX")

        variables = {
            "serverName": server_name,
            "baseUrl": base_url,
            "updatedBy": "test_user",
        }
        if bearer_token:
            variables["bearerToken"] = bearer_token
        if name_prefix:
            variables["namePrefix"] = name_prefix

        query = Graphql.generate_graphql_operation(
            "syncExternalMcpServer", "Mutation", self.schema
        )
        logger.info(f"Sync target: serverName={server_name}, baseUrl={base_url}")
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(
            query=query, variables=variables
        )
        logger.info(response)

        parsed = self._parse_graphql_response(response)["data"]["syncExternalMcpServer"]
        self.assertTrue(parsed["ok"], parsed)
        self.assertIsNotNone(parsed.get("stats"))

        stats = parsed["stats"]
        logger.info(
            f"Synced {server_name}: {stats['tools']} tools, "
            f"{stats['resources']} resources, {stats['prompts']} prompts, "
            f"{stats['modules']} modules, {stats['settings']} settings"
        )
        # At least one of the three inventories should be non-empty for a
        # useful test target; surface that as a clear failure if not.
        self.assertGreater(
            stats["tools"] + stats["resources"] + stats["prompts"],
            0,
            "Remote server returned an empty inventory — check the URL.",
        )
        # The handler always writes exactly one module and one shared setting.
        self.assertEqual(stats["modules"], 1)
        self.assertEqual(stats["settings"], 1)

    @unittest.skip("demonstrating skipping")
    def test_graphql_sync_external_mcp_server_invalid_name(self):
        """Negative path: invalid server name must be rejected before any
        HTTP or DB activity."""
        query = Graphql.generate_graphql_operation(
            "syncExternalMcpServer", "Mutation", self.schema
        )
        response = self.mcp_protocol_plugin.mcp_daemon_graphql(
            query=query,
            variables={
                "serverName": "bad-name",
                "baseUrl": "https://example.com/mcp",
                "updatedBy": "test_user",
            },
        )
        logger.info(response)
        parsed = self._parse_graphql_response(response)["data"]["syncExternalMcpServer"]
        self.assertFalse(parsed["ok"])
        self.assertIn("Invalid server name", parsed["message"])

    @unittest.skip("requires a previously synced external MCP server + live AWS")
    def test_mcp_call_external_search_product(self):
        """Invoke a 'search_product' tool that lives on a previously synced
        external MCP server. Routes through the daemon's MCP endpoint:

            agent -> mcp_server.call_tool -> execute_tool_function
                  -> ExternalMCPProxy.call_tool -> MCPHttpClient -> upstream

        Prerequisites:
            - test_graphql_sync_external_mcp_server has already run against
              the same partition, so the function/module/setting rows exist
              with source="external".

        Env:
            MCP_TEST_EXTERNAL_TOOL_NAME  - local tool name to invoke
                                           (default: "search_product").
                                           Must include MCP_TEST_EXTERNAL_NAME_PREFIX
                                           if one was used during sync.
            MCP_TEST_EXTERNAL_TOOL_QUERY - free-text query forwarded as the
                                           "query" argument (default: "shirt").
        """
        local_tool_name = os.getenv("MCP_TEST_EXTERNAL_TOOL_NAME", "search_product")
        query = os.getenv("MCP_TEST_EXTERNAL_TOOL_QUERY", "shirt")

        # Edit `arguments` to match the upstream tool's inputSchema. The
        # daemon validates required fields server-side via _validate_and_set_defaults.
        arguments = {"query": query}

        payload = {
            "method": "tools/call",
            "params": {
                "name": local_tool_name,
                "arguments": arguments,
            },
            "id": "1",
        }
        logger.info(f"Invoking external tool: {payload}")
        response = self.mcp_protocol_plugin.mcp(**payload)
        logger.info(response)

        # mcp() returns an HttpResponse-shaped dict; parse the JSON body and
        # walk to result.content[0].text without assuming a specific schema
        # past the MCP envelope.
        parsed = self._parse_graphql_response(response)
        self.assertNotIn("error", parsed, parsed)
        result = parsed.get("result") or {}
        content = result.get("content") or []
        self.assertTrue(
            content,
            f"Upstream returned no content. Full response: {parsed}",
        )
        first = content[0]
        self.assertIn("text", first, first)
        logger.info(f"search_product returned: {first['text'][:500]}")


if __name__ == "__main__":
    unittest.main()
