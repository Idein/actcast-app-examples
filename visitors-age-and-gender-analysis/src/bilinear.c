#include <math.h>
#include <stdint.h>

void bilinear_HWC_u8(
    const int32_t channel,
    const int32_t src_h, const int32_t src_w,
    const int32_t area_x, const int32_t area_y,
    const int32_t area_h, const int32_t area_w,
    const int32_t dst_h, const int32_t dst_w,
    const uint8_t* src, uint8_t* dst
) {
    (void)src_h; // unused
    for (int32_t oh = 0; oh < dst_h; ++oh) {
        const float v = fmaxf(0.0f, fminf((((oh + 0.5f) * area_h) / dst_h) - 0.5f, area_h - 1));
        const int32_t v0 = (int32_t)v;
        const int32_t v1 = v0 + 1u;
        const int32_t v0_ix = v0;
        const int32_t v1_ix = (v1 < (area_h - 1)) ? v1 : (area_h - 1);
        for (int32_t ow = 0u; ow < dst_w; ++ow) {
            const float u = fmaxf(0.0f, fminf((((ow + 0.5f) * area_w) / dst_w) - 0.5f, area_w - 1));
            const int32_t u0 = (int32_t)u;
            const int32_t u1 = u0 + 1;
            const float w00 = (u1 - u) * (v1 - v);
            const float w01 = (u - u0) * (v1 - v);
            const float w10 = (u1 - u) * (v - v0);
            const float w11 = (u - u0) * (v - v0);
            const int32_t u0_ix = u0;
            const int32_t u1_ix = (u1 < (area_w - 1)) ? u1 : (area_w - 1);
            for (int32_t ch = 0u; ch < channel; ++ch) {
              if(((v0_ix+area_y) < 0) ||
                 ((v1_ix+area_y) >= src_h) ||
                 ((u0_ix+area_x) < 0) ||
                 ((u1_ix+area_x) >= src_w)){
                dst[((oh*dst_w+ow)*channel)+ch] = 0;
              }else{
                dst[((oh*dst_w+ow)*channel)+ch] =
                    ((w00 * src[(((v0_ix+area_y)*src_w+(u0_ix+area_x))*channel)+ch]) +
                     (w01 * src[(((v0_ix+area_y)*src_w+(u1_ix+area_x))*channel)+ch])) +
                    ((w10 * src[(((v1_ix+area_y)*src_w+(u0_ix+area_x))*channel)+ch]) +
                     (w11 * src[(((v1_ix+area_y)*src_w+(u1_ix+area_x))*channel)+ch]));
              }
            }
        }
    }
}
