import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.task import Subtask, TaskStatus

logger = logging.getLogger(__name__)

class CodeGenerationAgent(BaseAgent):
    """Agent for code generation tasks."""
    
    async def execute(self, subtask: Subtask, context: Dict[str, Any] = None) -> Subtask:
        """
        Execute code generation for the given subtask.
        
        Args:
            subtask: The subtask to execute
            context: Additional context for task execution
            
        Returns:
            Updated subtask with results
        """
        logger.info(f"Starting code generation for subtask {subtask.id}")
        
        try:
            # Update status to in progress
            subtask.status = TaskStatus.IN_PROGRESS
            
            # Simulate code generation steps
            steps = [
                "Analyzing requirements",
                "Designing solution architecture",
                "Generating code structure",
                "Implementing functionality",
                "Adding documentation"
            ]
            
            # Process each step with progress updates
            total_steps = len(steps)
            for i, step in enumerate(steps):
                # Update progress
                progress = (i + 0.5) / total_steps
                await self.update_progress(subtask, progress, f"In progress: {step}")
                
                # Simulate work
                await asyncio.sleep(1)  # In a real implementation, this would be actual code generation
            
            # Generate simulated code results
            code_results = self._generate_code_example(context.get('task', '') if context else '')
            
            # Complete the subtask
            subtask.status = TaskStatus.COMPLETED
            subtask.progress = 1.0
            subtask.result = code_results
            subtask.updated_at = datetime.utcnow()
            
            logger.info(f"Completed code generation for subtask {subtask.id}")
            
        except Exception as e:
            error_msg = f"Error in code generation: {str(e)}"
            logger.error(error_msg)
            subtask.status = TaskStatus.FAILED
            subtask.error = error_msg
            subtask.updated_at = datetime.utcnow()
        
        return subtask
    
    def _generate_code_example(self, task_description: str) -> str:
        """Generate code example based on the task description."""
        # In a real implementation, this would generate actual code based on the task
        
        # Default to Python if no specific language is mentioned
        language = "python"
        if "javascript" in task_description.lower() or "js" in task_description.lower():
            language = "javascript"
        elif "java" in task_description.lower():
            language = "java"
        
        result = "## Generated Code Solution\n\n"
        
        if language == "python":
            result += "### Python Implementation\n\n"
            result += "```python\n"
            result += "import os\nimport json\nfrom typing import Dict, List, Any\n\n"
            result += "class DataProcessor:\n"
            result += "    def __init__(self, config_path: str = 'config.json'):\n"
            result += "        self.config = self._load_config(config_path)\n"
            result += "        self.processed_data = []\n\n"
            result += "    def _load_config(self, config_path: str) -> Dict[str, Any]:\n"
            result += "        \"\"\"Load configuration from a JSON file.\"\"\"\n"
            result += "        if not os.path.exists(config_path):\n"
            result += "            return {}\n"
            result += "        with open(config_path, 'r') as f:\n"
            result += "            return json.load(f)\n\n"
            result += "    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:\n"
            result += "        \"\"\"Process the input data according to configuration.\"\"\"\n"
            result += "        result = []\n"
            result += "        for item in data:\n"
            result += "            processed_item = self._transform_item(item)\n"
            result += "            if processed_item:\n"
            result += "                result.append(processed_item)\n"
            result += "        self.processed_data = result\n"
            result += "        return result\n\n"
            result += "    def _transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:\n"
            result += "        \"\"\"Transform a single data item.\"\"\"\n"
            result += "        # Apply transformations based on config\n"
            result += "        result = {}\n"
            result += "        for key, value in item.items():\n"
            result += "            if key in self.config.get('exclude_fields', []):\n"
            result += "                continue\n"
            result += "            if key in self.config.get('rename_fields', {}):\n"
            result += "                result[self.config['rename_fields'][key]] = value\n"
            result += "            else:\n"
            result += "                result[key] = value\n"
            result += "        return result\n\n"
            result += "    def save_results(self, output_path: str) -> None:\n"
            result += "        \"\"\"Save processed results to a JSON file.\"\"\"\n"
            result += "        with open(output_path, 'w') as f:\n"
            result += "            json.dump(self.processed_data, f, indent=2)\n\n"
            result += "# Example usage\n"
            result += "if __name__ == '__main__':\n"
            result += "    processor = DataProcessor('config.json')\n"
            result += "    data = [\n"
            result += "        {'id': 1, 'name': 'Item 1', 'value': 100},\n"
            result += "        {'id': 2, 'name': 'Item 2', 'value': 200},\n"
            result += "    ]\n"
            result += "    processed = processor.process_data(data)\n"
            result += "    processor.save_results('output.json')\n"
            result += "```\n\n"
        elif language == "javascript":
            result += "### JavaScript Implementation\n\n"
            result += "```javascript\n"
            result += "const fs = require('fs');\n\n"
            result += "class DataProcessor {\n"
            result += "  constructor(configPath = 'config.json') {\n"
            result += "    this.config = this._loadConfig(configPath);\n"
            result += "    this.processedData = [];\n"
            result += "  }\n\n"
            result += "  _loadConfig(configPath) {\n"
            result += "    try {\n"
            result += "      if (fs.existsSync(configPath)) {\n"
            result += "        const configData = fs.readFileSync(configPath, 'utf8');\n"
            result += "        return JSON.parse(configData);\n"
            result += "      }\n"
            result += "    } catch (error) {\n"
            result += "      console.error('Error loading config:', error);\n"
            result += "    }\n"
            result += "    return {};\n"
            result += "  }\n\n"
            result += "  processData(data) {\n"
            result += "    const result = [];\n"
            result += "    for (const item of data) {\n"
            result += "      const processedItem = this._transformItem(item);\n"
            result += "      if (processedItem) {\n"
            result += "        result.push(processedItem);\n"
            result += "      }\n"
            result += "    }\n"
            result += "    this.processedData = result;\n"
            result += "    return result;\n"
            result += "  }\n\n"
            result += "  _transformItem(item) {\n"
            result += "    const result = {};\n"
            result += "    const excludeFields = this.config.exclude_fields || [];\n"
            result += "    const renameFields = this.config.rename_fields || {};\n\n"
            result += "    for (const [key, value] of Object.entries(item)) {\n"
            result += "      if (excludeFields.includes(key)) {\n"
            result += "        continue;\n"
            result += "      }\n"
            result += "      if (key in renameFields) {\n"
            result += "        result[renameFields[key]] = value;\n"
            result += "      } else {\n"
            result += "        result[key] = value;\n"
            result += "      }\n"
            result += "    }\n"
            result += "    return result;\n"
            result += "  }\n\n"
            result += "  saveResults(outputPath) {\n"
            result += "    try {\n"
            result += "      fs.writeFileSync(outputPath, JSON.stringify(this.processedData, null, 2));\n"
            result += "      console.log(`Results saved to ${outputPath}`);\n"
            result += "    } catch (error) {\n"
            result += "      console.error('Error saving results:', error);\n"
            result += "    }\n"
            result += "  }\n"
            result += "}\n\n"
            result += "// Example usage\n"
            result += "const processor = new DataProcessor('config.json');\n"
            result += "const data = [\n"
            result += "  { id: 1, name: 'Item 1', value: 100 },\n"
            result += "  { id: 2, name: 'Item 2', value: 200 },\n"
            result += "];\n"
            result += "const processed = processor.processData(data);\n"
            result += "processor.saveResults('output.json');\n"
            result += "```\n\n"
        else:
            result += "### Java Implementation\n\n"
            result += "```java\n"
            result += "import java.io.*;\n"
            result += "import java.util.*;\n"
            result += "import org.json.simple.*;\n"
            result += "import org.json.simple.parser.*;\n\n"
            result += "public class DataProcessor {\n"
            result += "    private JSONObject config;\n"
            result += "    private JSONArray processedData;\n\n"
            result += "    public DataProcessor(String configPath) {\n"
            result += "        this.config = loadConfig(configPath);\n"
            result += "        this.processedData = new JSONArray();\n"
            result += "    }\n\n"
            result += "    private JSONObject loadConfig(String configPath) {\n"
            result += "        try {\n"
            result += "            File file = new File(configPath);\n"
            result += "            if (file.exists()) {\n"
            result += "                JSONParser parser = new JSONParser();\n"
            result += "                return (JSONObject) parser.parse(new FileReader(file));\n"
            result += "            }\n"
            result += "        } catch (Exception e) {\n"
            result += "            System.err.println(\"Error loading config: \" + e.getMessage());\n"
            result += "        }\n"
            result += "        return new JSONObject();\n"
            result += "    }\n\n"
            result += "    public JSONArray processData(JSONArray data) {\n"
            result += "        JSONArray result = new JSONArray();\n"
            result += "        for (Object item : data) {\n"
            result += "            JSONObject processedItem = transformItem((JSONObject) item);\n"
            result += "            if (processedItem != null) {\n"
            result += "                result.add(processedItem);\n"
            result += "            }\n"
            result += "        }\n"
            result += "        this.processedData = result;\n"
            result += "        return result;\n"
            result += "    }\n\n"
            result += "    private JSONObject transformItem(JSONObject item) {\n"
            result += "        JSONObject result = new JSONObject();\n"
            result += "        JSONArray excludeFields = (JSONArray) config.getOrDefault(\"exclude_fields\", new JSONArray());\n"
            result += "        JSONObject renameFields = (JSONObject) config.getOrDefault(\"rename_fields\", new JSONObject());\n\n"
            result += "        for (Object keyObj : item.keySet()) {\n"
            result += "            String key = (String) keyObj;\n"
            result += "            if (excludeFields.contains(key)) {\n"
            result += "                continue;\n"
            result += "            }\n"
            result += "            if (renameFields.containsKey(key)) {\n"
            result += "                result.put(renameFields.get(key), item.get(key));\n"
            result += "            } else {\n"
            result += "                result.put(key, item.get(key));\n"
            result += "            }\n"
            result += "        }\n"
            result += "        return result;\n"
            result += "    }\n\n"
            result += "    public void saveResults(String outputPath) {\n"
            result += "        try (FileWriter file = new FileWriter(outputPath)) {\n"
            result += "            file.write(processedData.toJSONString());\n"
            result += "            System.out.println(\"Results saved to \" + outputPath);\n"
            result += "        } catch (IOException e) {\n"
            result += "            System.err.println(\"Error saving results: \" + e.getMessage());\n"
            result += "        }\n"
            result += "    }\n\n"
            result += "    public static void main(String[] args) {\n"
            result += "        DataProcessor processor = new DataProcessor(\"config.json\");\n"
            result += "        JSONArray data = new JSONArray();\n"
            result += "        \n"
            result += "        JSONObject item1 = new JSONObject();\n"
            result += "        item1.put(\"id\", 1);\n"
            result += "        item1.put(\"name\", \"Item 1\");\n"
            result += "        item1.put(\"value\", 100);\n"
            result += "        data.add(item1);\n"
            result += "        \n"
            result += "        JSONObject item2 = new JSONObject();\n"
            result += "        item2.put(\"id\", 2);\n"
            result += "        item2.put(\"name\", \"Item 2\");\n"
            result += "        item2.put(\"value\", 200);\n"
            result += "        data.add(item2);\n"
            result += "        \n"
            result += "        processor.processData(data);\n"
            result += "        processor.saveResults(\"output.json\");\n"
            result += "    }\n"
            result += "}\n"
            result += "```\n\n"
        
        result += "### Usage Instructions\n\n"
        result += "1. Create a `config.json` file with the following structure:\n"
        result += "```json\n"
        result += "{\n"
        result += "  \"exclude_fields\": [\"field_to_exclude\"],\n"
        result += "  \"rename_fields\": {\n"
        result += "    \"original_name\": \"new_name\"\n"
        result += "  }\n"
        result += "}\n"
        result += "```\n\n"
        result += "2. Initialize the `DataProcessor` with your config file\n"
        result += "3. Call `process_data()` with your input data\n"
        result += "4. Use `save_results()` to save the processed data to a file\n"
        
        return result
