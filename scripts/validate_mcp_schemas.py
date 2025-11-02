#!/usr/bin/env python3
"""
Validate MCP tool schemas for Orbit-MCP.

This script ensures all tools follow the MCP protocol specification
and have valid JSON schemas.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def validate_tool_schema(tool: Dict[str, Any]) -> List[str]:
    """
    Validate a single tool schema.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Required fields
    required_fields = ['name', 'description', 'inputSchema']
    for field in required_fields:
        if field not in tool:
            errors.append(f"Missing required field: {field}")
    
    # Name format
    if 'name' in tool:
        name = tool['name']
        if not isinstance(name, str):
            errors.append(f"Tool name must be string, got {type(name)}")
        elif '.' not in name:
            errors.append(f"Tool name should follow 'category.action' format: {name}")
    
    # Description
    if 'description' in tool:
        desc = tool['description']
        if not isinstance(desc, str):
            errors.append(f"Description must be string")
        elif len(desc) < 10:
            errors.append(f"Description too short: {desc}")
    
    # Input schema
    if 'inputSchema' in tool:
        schema = tool['inputSchema']
        if not isinstance(schema, dict):
            errors.append(f"inputSchema must be dict")
        else:
            # Validate JSON Schema structure
            if 'type' not in schema:
                errors.append(f"inputSchema missing 'type' field")
            
            if schema.get('type') == 'object' and 'properties' not in schema:
                errors.append(f"Object schema missing 'properties'")
            
            # Check for required fields definition
            if 'properties' in schema:
                props = schema['properties']
                if not isinstance(props, dict):
                    errors.append(f"properties must be dict")
                
                # Each property should have a type
                for prop_name, prop_schema in props.items():
                    if not isinstance(prop_schema, dict):
                        errors.append(f"Property {prop_name} schema must be dict")
                    elif 'type' not in prop_schema and '$ref' not in prop_schema:
                        errors.append(f"Property {prop_name} missing type")
    
    return errors


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Load tool definitions from Orbit-MCP.
    
    This is a placeholder - in real implementation, this would
    import from the actual MCP server code.
    """
    # Example tool definitions
    tools = [
        {
            'name': 'ssh.run',
            'description': 'Execute a command on a remote server via SSH',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'host': {
                        'type': 'string',
                        'description': 'Target host identifier'
                    },
                    'command': {
                        'type': 'string',
                        'description': 'Command to execute'
                    },
                    'timeout': {
                        'type': 'integer',
                        'description': 'Command timeout in seconds',
                        'default': 30
                    }
                },
                'required': ['host', 'command']
            }
        },
        {
            'name': 'k8s.get',
            'description': 'Get Kubernetes resources',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'kind': {
                        'type': 'string',
                        'enum': ['pods', 'services', 'deployments'],
                        'description': 'Resource kind'
                    },
                    'namespace': {
                        'type': 'string',
                        'description': 'Namespace to query',
                        'default': 'default'
                    },
                    'selector': {
                        'type': 'string',
                        'description': 'Label selector'
                    }
                },
                'required': ['kind']
            }
        },
        {
            'name': 'docker.logs',
            'description': 'Retrieve logs from a Docker container',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'container': {
                        'type': 'string',
                        'description': 'Container ID or name'
                    },
                    'lines': {
                        'type': 'integer',
                        'description': 'Number of lines to retrieve',
                        'default': 100
                    },
                    'follow': {
                        'type': 'boolean',
                        'description': 'Follow log output',
                        'default': False
                    }
                },
                'required': ['container']
            }
        },
        {
            'name': 'llm.chat',
            'description': 'Chat with an LLM',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'description': 'User prompt'
                    },
                    'provider': {
                        'type': 'string',
                        'enum': ['openai', 'anthropic', 'ollama'],
                        'description': 'LLM provider to use'
                    },
                    'temperature': {
                        'type': 'number',
                        'description': 'Sampling temperature',
                        'minimum': 0.0,
                        'maximum': 2.0,
                        'default': 0.7
                    }
                },
                'required': ['prompt']
            }
        }
    ]
    
    return tools


def main():
    """Main validation function."""
    print("=== Orbit-MCP Tool Schema Validator ===\n")
    
    tools = get_tool_definitions()
    
    print(f"Found {len(tools)} tool(s) to validate\n")
    
    all_valid = True
    
    for tool in tools:
        tool_name = tool.get('name', '<unnamed>')
        print(f"Validating: {tool_name}")
        
        errors = validate_tool_schema(tool)
        
        if errors:
            all_valid = False
            print(f"  ? FAILED with {len(errors)} error(s):")
            for error in errors:
                print(f"     - {error}")
        else:
            print(f"  ? PASSED")
        
        print()
    
    # Summary
    print("=" * 50)
    if all_valid:
        print("? All tools passed validation!")
        return 0
    else:
        print("? Some tools failed validation")
        return 1


if __name__ == '__main__':
    sys.exit(main())
