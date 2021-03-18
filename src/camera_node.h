typedef void* camera_node_t;

camera_node_t CreateCameraNode(int width, int height);
void PublishImage(const camera_node_t camera_node, char* image_data);
void DeleteCameraNode(camera_node_t node);
