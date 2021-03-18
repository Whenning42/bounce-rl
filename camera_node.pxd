cdef extern from "src/camera_node.h":
    ctypedef void* camera_node_t
    camera_node_t CreateCameraNode(int width, int height)
    void PublishImage(camera_node_t camera_node, char *data)
    void DeleteCameraNode(camera_node_t camera_node)
