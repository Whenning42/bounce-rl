#include <string>
#include <vulkan/vulkan.h>
#include <stdio.h>
#include <vector>
#include <cassert>
#include <fstream>
#include <iostream>

struct Program {
  VkInstance instance;
  VkDebugUtilsMessengerEXT debug_utils_messenger;
  VkPhysicalDevice physical_device;
  VkDevice device;
  VkPipelineLayout pipeline_layout;
  VkPipeline pipeline;
  VkShaderModule shader_module;
  VkCommandPool command_pool;
  VkCommandBuffer command_buffer;
  VkDescriptorPool descriptor_pool;
  VkDescriptorSetLayout descriptor_set_layout;
  VkDescriptorSet descriptor_set;
  VkShaderModule compute_shader_module;

  // These should maybe be split out?
  // - Send buffer
  // - Recieve buffer
  VkBuffer image_buffer;
  VkDeviceMemory image_buffer_memory;
  uint32_t image_buffer_size = 1024 * 1024;

  VkBuffer encoded_buffer;
  VkDeviceMemory encoded_buffer_memory;
  uint32_t encoded_buffer_size = 1024 * 1024;

  VkQueue queue;
  uint32_t queue_family_index;
};

bool LayerIsPresent(const std::string& layer) {
    uint32_t layer_count;
    vkEnumerateInstanceLayerProperties(&layer_count, nullptr);
    std::vector<VkLayerProperties> layer_properties(layer_count);
    vkEnumerateInstanceLayerProperties(&layer_count, layer_properties.data());

    bool found = false;
    for (VkLayerProperties properties : layer_properties) {
      if (layer == std::string(properties.layerName)) {
        found = true;
        break;
      }
    }
    return found;
}

bool ExtensionIsPresent(const std::string& extension) {
    uint32_t extension_count;
    vkEnumerateInstanceExtensionProperties(nullptr, &extension_count, nullptr);
    std::vector<VkExtensionProperties> extension_properties(extension_count);
    vkEnumerateInstanceExtensionProperties(nullptr, &extension_count, extension_properties.data());

    bool found = false;
    for (VkExtensionProperties properties : extension_properties) {
      if (extension == std::string(properties.extensionName)) {
        found = true;
        break;
      }
    }
    return found;
}

void EnforceLayer(const std::string& layer) {
  if (!LayerIsPresent(layer)) {
    printf("Failed to find required layer %s\n, exiting.", layer.c_str());
  }
}

void EnforceExtension(const std::string& extension) {
  if (!ExtensionIsPresent(extension)) {
    printf("Failed to find required extension %s\n, exiting.", extension.c_str());
  }
}

void AssertOK(bool v) {
  assert(!v);
}

std::vector<uint8_t> ReadFile(std::string filename) {
  std::ifstream infile(filename);

  infile.seekg(0, std::ios::end);
  size_t length = infile.tellg();
  if (length % 4 != 0) {
    length += 4 - length % 4;
  }
  infile.seekg(0, std::ios::beg);

  std::vector<char> file(length);
  infile.read(file.data(), length);
  return std::vector<uint8_t>(file.begin(), file.end());
}

VKAPI_ATTR VkBool32 VKAPI_CALL debug_utils_messenger_callback(
    VkDebugUtilsMessageSeverityFlagBitsEXT message_severity,
    VkDebugUtilsMessageTypeFlagsEXT message_type,
    const VkDebugUtilsMessengerCallbackDataEXT *callback_data,
    void *user_data)
{
	if (message_severity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT) {
    std::cout << "Warning: " << callback_data->messageIdNumber << ":" << callback_data->pMessageIdName << ":" <<  callback_data->pMessage << std::endl;
	} else if (message_severity & VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT) {
    std::cerr << "Error: " << callback_data->messageIdNumber << ":" << callback_data->pMessageIdName << ":" <<  callback_data->pMessage << std::endl;
	}
	return VK_FALSE;
}

// QOL fixes
//  - Scan/Find semantics for enumerations.
//  - Default sType assignment
//  - Nested structs instead of pointers
//  - Strings instead of const char**
//  - Vectors instead of length data pairs
//  - No allocators
//
// Wrapper fixes
//  - Minimal argument helpers
//  - Unified error handling?
//  - Beefiest physical device, single device, minimal queue setup.
int main(int argc, char** argv) {
  Program program;
  std::vector<std::string> layers = {"VK_LAYER_KHRONOS_validation"};
  std::vector<std::string> extensions = {VK_EXT_DEBUG_UTILS_EXTENSION_NAME};
  { // Create Instance
    const std::string app_name = "Compression";
    const std::string engine_name = "Whengine";
    const uint32_t api_version = VK_API_VERSION_1_2;
    const bool validate = true;
    int debug_report_bits = VK_DEBUG_REPORT_ERROR_BIT_EXT |
                            VK_DEBUG_REPORT_WARNING_BIT_EXT |
                            VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT;

    for (const std::string& layer : layers) {
      EnforceLayer(layer);
    }
    for (const std::string& extension : extensions) {
      EnforceExtension(extension);
    }

    VkApplicationInfo application_info = {};
    application_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    application_info.pApplicationName = app_name.c_str();
    application_info.pEngineName = engine_name.c_str();
    application_info.apiVersion = api_version;

    VkInstanceCreateInfo instance_create_info = {};
    instance_create_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    instance_create_info.pApplicationInfo = &application_info;

    if (validate) {
      layers.push_back("VK_LAYER_KHRONOS_validation");
      extensions.push_back(VK_EXT_DEBUG_UTILS_EXTENSION_NAME);
    }

    std::vector<const char*> layers_c_str;
    std::vector<const char*> extensions_c_str;
    for (const std::string& layer : layers) {
      layers_c_str.push_back(layer.c_str());
    }
    for (const std::string& extension : extensions) {
      extensions_c_str.push_back(extension.c_str());
    }

    if (validate) {
      VkDebugUtilsMessengerCreateInfoEXT debug_utils_create_info = {};
      debug_utils_create_info.sType = VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT;
      debug_utils_create_info.messageSeverity = VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT | VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT;
      debug_utils_create_info.messageType = VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT;
      debug_utils_create_info.pfnUserCallback = debug_utils_messenger_callback;

      instance_create_info.enabledLayerCount = layers.size();
      instance_create_info.ppEnabledLayerNames = layers_c_str.data();
      instance_create_info.enabledExtensionCount = extensions.size();
      instance_create_info.ppEnabledExtensionNames = extensions_c_str.data();
      instance_create_info.pNext = &debug_utils_create_info;
      AssertOK(vkCreateInstance(&instance_create_info, nullptr, &program.instance));

      auto vkCreateDebugUtilsMessengerEXT = (PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(program.instance, "vkCreateDebugUtilsMessengerEXT");
      assert(vkCreateDebugUtilsMessengerEXT);

      AssertOK(vkCreateDebugUtilsMessengerEXT(program.instance, &debug_utils_create_info, nullptr, &program.debug_utils_messenger));
    } else {
      AssertOK(vkCreateInstance(&instance_create_info, nullptr, &program.instance));
    }
  }

  { // Set PhysicalDevice, Device, QueueFamily, and Queue, takes in layers.
    uint32_t device_count;
    vkEnumeratePhysicalDevices(program.instance, &device_count, nullptr);
    std::vector<VkPhysicalDevice> devices(device_count);
    vkEnumeratePhysicalDevices(program.instance, &device_count, devices.data());
    assert(device_count > 0);
    program.physical_device = devices[0];

    uint32_t queue_family_count;
    vkGetPhysicalDeviceQueueFamilyProperties(program.physical_device, &queue_family_count, nullptr);
    std::vector<VkQueueFamilyProperties> queue_families(queue_family_count);
    vkGetPhysicalDeviceQueueFamilyProperties(program.physical_device, &queue_family_count, queue_families.data());

    uint32_t i = 0;
    while (i < queue_families.size()) {
      if (queue_families[i].queueCount > 0 && (queue_families[i].queueFlags & VK_QUEUE_COMPUTE_BIT)) {
        break;
      }
      i++;
      assert(i != queue_families.size());
    }
    program.queue_family_index = i;

    VkDeviceQueueCreateInfo queue_create_info = {};
    queue_create_info.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    queue_create_info.queueFamilyIndex = program.queue_family_index;
    queue_create_info.queueCount = 1;
    float queue_priority = 1.0;
    queue_create_info.pQueuePriorities = &queue_priority;

    VkDeviceCreateInfo device_create_info = {};
    VkPhysicalDeviceFeatures device_features = {};

    std::vector<const char*> layers_c_str;
    for (const std::string& layer : layers) {
      layers_c_str.push_back(layer.c_str());
    }
    device_create_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    device_create_info.enabledLayerCount = layers.size();
    device_create_info.ppEnabledLayerNames = layers_c_str.data();
    device_create_info.pQueueCreateInfos = &queue_create_info;
    device_create_info.queueCreateInfoCount = 1;
    device_create_info.pEnabledFeatures = &device_features;

    AssertOK(vkCreateDevice(program.physical_device, &device_create_info, nullptr, &program.device));
    vkGetDeviceQueue(program.device, program.queue_family_index, 0, &program.queue);
  }

  { // Create buffer and allocate its memory.
    VkBufferCreateInfo buffer_create_info = {};
    buffer_create_info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    buffer_create_info.size = program.image_buffer_size;
    buffer_create_info.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    buffer_create_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    AssertOK(vkCreateBuffer(program.device, &buffer_create_info, nullptr, &program.image_buffer));

    buffer_create_info.size = program.encoded_buffer_size;
    AssertOK(vkCreateBuffer(program.device, &buffer_create_info, nullptr, &program.encoded_buffer));

    VkMemoryRequirements memory_requirements;
    vkGetBufferMemoryRequirements(program.device, program.image_buffer, &memory_requirements);

    VkPhysicalDeviceMemoryProperties memory_properties;
    vkGetPhysicalDeviceMemoryProperties(program.physical_device, &memory_properties);
    VkMemoryPropertyFlags memory_property_flags = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT;
    uint32_t memory_type_index;
    for (uint32_t i = 0;  i < memory_properties.memoryTypeCount; ++i) {
      if ((memory_requirements.memoryTypeBits & (1 << i) &&
          (memory_properties.memoryTypes[i].propertyFlags & memory_property_flags) == memory_property_flags)) {
        memory_type_index = i;
        break;
      }
      assert(i != memory_properties.memoryTypeCount - 1);
    }

    VkMemoryAllocateInfo allocate_info = {};
    allocate_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    allocate_info.allocationSize = memory_requirements.size;
    allocate_info.memoryTypeIndex = memory_type_index;
    AssertOK(vkAllocateMemory(program.device, &allocate_info, nullptr, &program.image_buffer_memory));
    AssertOK(vkBindBufferMemory(program.device, program.image_buffer, program.image_buffer_memory, 0));

    AssertOK(vkAllocateMemory(program.device, &allocate_info, nullptr, &program.encoded_buffer_memory));
    AssertOK(vkBindBufferMemory(program.device, program.encoded_buffer, program.encoded_buffer_memory, 0));
  }

  { // Create descriptor set layout and set.
    VkDescriptorSetLayoutBinding image_binding = {};
    image_binding.binding = 0;
    image_binding.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    image_binding.descriptorCount = 1;
    image_binding.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;

    VkDescriptorSetLayoutBinding encoded_binding = {};
    encoded_binding.binding = 1;
    encoded_binding.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    encoded_binding.descriptorCount = 1;
    encoded_binding.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    std::vector<VkDescriptorSetLayoutBinding> bindings = {image_binding, encoded_binding};

    VkDescriptorSetLayoutCreateInfo descriptor_set_layout_create_info = {};
    descriptor_set_layout_create_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    descriptor_set_layout_create_info.bindingCount = bindings.size();
    descriptor_set_layout_create_info.pBindings = bindings.data();
    AssertOK(vkCreateDescriptorSetLayout(program.device, &descriptor_set_layout_create_info, nullptr, &program.descriptor_set_layout));

    // One pool or two?
    VkDescriptorPoolSize image_pool_size = {};
    image_pool_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    image_pool_size.descriptorCount = 1;

    VkDescriptorPoolSize encoded_pool_size = {};
    encoded_pool_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    encoded_pool_size.descriptorCount = 1;

    std::vector<VkDescriptorPoolSize> pool_sizes = {image_pool_size, encoded_pool_size};

    VkDescriptorPoolCreateInfo descriptor_pool_create_info = {};
    descriptor_pool_create_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    descriptor_pool_create_info.maxSets = 1;
    descriptor_pool_create_info.poolSizeCount = pool_sizes.size();
    descriptor_pool_create_info.pPoolSizes = pool_sizes.data();
    AssertOK(vkCreateDescriptorPool(program.device, &descriptor_pool_create_info, nullptr, &program.descriptor_pool));

    VkDescriptorSetAllocateInfo descriptor_set_allocate_info = {};
    descriptor_set_allocate_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    descriptor_set_allocate_info.descriptorPool = program.descriptor_pool;
    descriptor_set_allocate_info.descriptorSetCount = 1;
    descriptor_set_allocate_info.pSetLayouts = &program.descriptor_set_layout;
    AssertOK(vkAllocateDescriptorSets(program.device, &descriptor_set_allocate_info, &program.descriptor_set));

    VkDescriptorBufferInfo image_buffer_info = {};
    image_buffer_info.buffer = program.image_buffer;
    image_buffer_info.offset = 0;
    image_buffer_info.range = program.image_buffer_size;

    VkDescriptorBufferInfo encoded_buffer_info = {};
    encoded_buffer_info.buffer = program.encoded_buffer;
    encoded_buffer_info.offset = 0;
    encoded_buffer_info.range = program.encoded_buffer_size;

    VkWriteDescriptorSet write_image_descriptor_set = {};
    write_image_descriptor_set.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write_image_descriptor_set.dstSet = program.descriptor_set;
    write_image_descriptor_set.dstBinding = 0;
    write_image_descriptor_set.descriptorCount = 1;
    write_image_descriptor_set.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write_image_descriptor_set.pBufferInfo = &image_buffer_info;
    vkUpdateDescriptorSets(program.device, 1, &write_image_descriptor_set, 0, nullptr);

    VkWriteDescriptorSet write_encoded_descriptor_set = {};
    write_encoded_descriptor_set.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write_encoded_descriptor_set.dstSet = program.descriptor_set;
    write_encoded_descriptor_set.dstBinding = 1;
    write_encoded_descriptor_set.descriptorCount = 1;
    write_encoded_descriptor_set.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write_encoded_descriptor_set.pBufferInfo = &encoded_buffer_info;
    vkUpdateDescriptorSets(program.device, 1, &write_encoded_descriptor_set, 0, nullptr);
  }

  { // Create compute pipeline
    std::vector<uint8_t> shader = ReadFile("comp.spv");
    VkShaderModuleCreateInfo create_info = {};
    create_info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    create_info.pCode = (uint32_t*)shader.data();
    create_info.codeSize = shader.size();
    AssertOK(vkCreateShaderModule(program.device, &create_info, nullptr, &program.compute_shader_module));

    VkPipelineShaderStageCreateInfo shader_stage_create_info = {};
    shader_stage_create_info.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    shader_stage_create_info.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    shader_stage_create_info.module = program.compute_shader_module;
    shader_stage_create_info.pName = "main";

    VkPipelineLayoutCreateInfo pipeline_layout_create_info = {};
    pipeline_layout_create_info.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pipeline_layout_create_info.setLayoutCount = 1;
    pipeline_layout_create_info.pSetLayouts = &program.descriptor_set_layout;
    AssertOK(vkCreatePipelineLayout(program.device, &pipeline_layout_create_info, nullptr, &program.pipeline_layout));

    VkComputePipelineCreateInfo pipeline_create_info = {};
    pipeline_create_info.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    pipeline_create_info.stage = shader_stage_create_info;
    pipeline_create_info.layout = program.pipeline_layout;
    AssertOK(vkCreateComputePipelines(program.device, VK_NULL_HANDLE, 1, &pipeline_create_info, nullptr, &program.pipeline));
  }

  { // Create command buffer
    VkCommandPoolCreateInfo command_pool_create_info = {};
    command_pool_create_info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    command_pool_create_info.flags = 0;
    command_pool_create_info.queueFamilyIndex = program.queue_family_index;
    AssertOK(vkCreateCommandPool(program.device, &command_pool_create_info, nullptr, &program.command_pool));

    VkCommandBufferAllocateInfo command_buffer_allocate_info = {};
    command_buffer_allocate_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    command_buffer_allocate_info.commandPool = program.command_pool;
    command_buffer_allocate_info.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    command_buffer_allocate_info.commandBufferCount = 1;
    AssertOK(vkAllocateCommandBuffers(program.device, &command_buffer_allocate_info, &program.command_buffer));

    VkCommandBufferBeginInfo begin_info = {};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    AssertOK(vkBeginCommandBuffer(program.command_buffer, &begin_info));

    vkCmdBindPipeline(program.command_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, program.pipeline);
    vkCmdBindDescriptorSets(program.command_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, program.pipeline_layout, 0, 1, &program.descriptor_set, 0, NULL);
    vkCmdDispatch(program.command_buffer, 1, 1, 1);
    AssertOK(vkEndCommandBuffer(program.command_buffer));
  }

  { // Write image data to image buffer.
    void* mapped_memory = nullptr;
    vkMapMemory(program.device, program.image_buffer_memory, 0, program.image_buffer_size, 0, &mapped_memory);
    for (int i = 0; i < 1000; ++i) {
      ((uint32_t*)mapped_memory)[i] = i / 20;
    }
    VkMappedMemoryRange range;
    range.sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;
    range.memory = program.image_buffer_memory;
    range.offset = 0;
    range.size = program.image_buffer_size;
    vkFlushMappedMemoryRanges(program.device, 1, &range);
    vkUnmapMemory(program.device, program.image_buffer_memory);
  }

  { // Run command buffer
    VkSubmitInfo submit_info = {};
    submit_info.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit_info.commandBufferCount = 1;
    submit_info.pCommandBuffers = &program.command_buffer;

    VkFence fence;
    VkFenceCreateInfo fence_create_info = {};
    fence_create_info.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fence_create_info.flags = 0;
    AssertOK(vkCreateFence(program.device, &fence_create_info, nullptr, &fence));

    AssertOK(vkQueueSubmit(program.queue, 1, &submit_info, fence));
    AssertOK(vkWaitForFences(program.device, 1, &fence, VK_TRUE, 30l * 1000 * 1000 * 1000)); // 30s
    vkDestroyFence(program.device, fence, nullptr);
  }

  { // Read output result
    void* image_memory = nullptr;
    vkMapMemory(program.device, program.image_buffer_memory, 0, program.image_buffer_size, 0, &image_memory);
    for (int i = 0; i < 150; ++i) {
      printf("In[%d]: %d\n", i, ((uint32_t*)image_memory)[i]);
    }
    vkUnmapMemory(program.device, program.image_buffer_memory);

    void* mapped_memory = nullptr;
    vkMapMemory(program.device, program.encoded_buffer_memory, 0, program.encoded_buffer_size, 0, &mapped_memory);
    for (int i = 0; i < 150; ++i) {
      printf("Out[%d]: %d\n", i, ((uint32_t*)mapped_memory)[i]);
    }
    vkUnmapMemory(program.device, program.encoded_buffer_memory);
  }

  { // Cleanup
    // None.
  }
}
