#include <assert.h>
#include "hailo/hailort.h"

#define MAX_EDGE_LAYERS (16)
#define HEF_FILE ("resnet_v1_18.hef")

static hailo_vdevice vdevice = NULL;
static hailo_hef hef = NULL;
static hailo_configure_params_t config_params = {0};
static hailo_configured_network_group network_group = NULL;
static size_t network_group_size = 1;
static hailo_input_vstream_params_by_name_t input_vstream_params[MAX_EDGE_LAYERS] = {0};
static hailo_output_vstream_params_by_name_t output_vstream_params[MAX_EDGE_LAYERS] = {0};
static hailo_activated_network_group activated_network_group = NULL;
static size_t vstreams_infos_size = MAX_EDGE_LAYERS;
static hailo_vstream_info_t vstreams_infos[MAX_EDGE_LAYERS] = {0};
static hailo_input_vstream input_vstreams[MAX_EDGE_LAYERS] = {NULL};
static hailo_output_vstream output_vstreams[MAX_EDGE_LAYERS] = {NULL};
static size_t input_vstreams_size = MAX_EDGE_LAYERS;
static size_t output_vstreams_size = MAX_EDGE_LAYERS;

int infer(unsigned char *input0, float *out0)
{
    unsigned char q_out0[1000];
    hailo_status status = HAILO_UNINITIALIZED;
    /* Feed Data */
    status = hailo_vstream_write_raw_buffer(input_vstreams[0], input0, 224 * 224 * 3);
    assert(status == HAILO_SUCCESS);
    status = hailo_flush_input_vstream(input_vstreams[0]);
    assert(status == HAILO_SUCCESS);

    status = hailo_vstream_read_raw_buffer(output_vstreams[0], q_out0, 1000);
    assert(status == HAILO_SUCCESS);
    /* dequantize */

    float scale = vstreams_infos[1].quant_info.qp_scale;
    float zp = vstreams_infos[1].quant_info.qp_zp;
    for (int i = 0; i < 1000; i++)
        out0[i] = scale * (q_out0[i] - zp);

    return status;
}

int init()
{
    hailo_status status = HAILO_UNINITIALIZED;

    status = hailo_create_vdevice(NULL, &vdevice);
    assert(status == HAILO_SUCCESS);

    status = hailo_create_hef_file(&hef, HEF_FILE);
    assert(status == HAILO_SUCCESS);

    status = hailo_init_configure_params(hef, HAILO_STREAM_INTERFACE_PCIE, &config_params);
    assert(status == HAILO_SUCCESS);

    status = hailo_configure_vdevice(vdevice, hef, &config_params, &network_group, &network_group_size);
    assert(status == HAILO_SUCCESS);

    status = hailo_make_input_vstream_params(network_group, true, HAILO_FORMAT_TYPE_AUTO,
        input_vstream_params, &input_vstreams_size);
    assert(status == HAILO_SUCCESS);

    status = hailo_make_output_vstream_params(network_group, true, HAILO_FORMAT_TYPE_AUTO,
        output_vstream_params, &output_vstreams_size);
    assert(status == HAILO_SUCCESS);

    status = hailo_hef_get_all_vstream_infos(hef, NULL, vstreams_infos, &vstreams_infos_size);
    assert(status == HAILO_SUCCESS);

    status = hailo_create_input_vstreams(network_group, input_vstream_params, input_vstreams_size, input_vstreams);
    assert(status == HAILO_SUCCESS);

    status = hailo_create_output_vstreams(network_group, output_vstream_params, output_vstreams_size, output_vstreams);
    assert(status == HAILO_SUCCESS);

    /* status = hailo_activate_network_group(network_group, NULL, &activated_network_group); */
    /* assert(status == HAILO_SUCCESS); */

    return status;
}

void destroy() {
    (void) hailo_deactivate_network_group(activated_network_group);
    (void) hailo_release_output_vstreams(output_vstreams, output_vstreams_size);
    (void) hailo_release_input_vstreams(input_vstreams, input_vstreams_size);
    (void) hailo_release_hef(hef);
    (void) hailo_release_vdevice(vdevice);
}
