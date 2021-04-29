/****************************************************************************
*
*    2020 Danyang Song (Arthur)
*    songdanyang@jiangxing.ai
*
*****************************************************************************/


#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <fstream>
#include <iostream>
#include <sys/time.h>
#include <sys/types.h>

#include "opencv2/core/core.hpp"
#include "opencv2/imgproc.hpp"
#include "opencv2/imgcodecs.hpp"

#include "rknn_api.h"

using namespace std;
using namespace cv;

#define BUFFERS_SIZE 512
#define kPIPE_I_PATH "/tmp/tcore_i"
#define kPIPE_O_PATH "/tmp/tcore_o"

#define kIMG_H 224
#define kIMG_W 224
#define kIMG_C 3            // channel

#define ERRNO_BROKEN_PIPE 1

static void printRKNNTensor(rknn_tensor_attr *attr) {
    printf("index=%d name=%s n_dims=%d dims=[%d %d %d %d] n_elems=%d size=%d fmt=%d type=%d qnt_type=%d fl=%d zp=%d scale=%f\n", 
            attr->index, attr->name, attr->n_dims, attr->dims[3], attr->dims[2], attr->dims[1], attr->dims[0], 
            attr->n_elems, attr->size, 0, attr->type, attr->qnt_type, attr->fl, attr->zp, attr->scale);
}

static unsigned char *load_model(const char *filename, int *model_size) {
    FILE *fp = fopen(filename, "rb");
    if(fp == nullptr) {
        printf("fopen %s fail!\n", filename);
        return NULL;
    }
    fseek(fp, 0, SEEK_END);
    int model_len = ftell(fp);
    unsigned char *model = (unsigned char*)malloc(model_len);
    fseek(fp, 0, SEEK_SET);
    if(model_len != fread(model, 1, model_len, fp)) {
        printf("fread %s fail!\n", filename);
        free(model);
        return NULL;
    }
    *model_size = model_len;
    if(fp) {
        fclose(fp);
    }
    return model;
}

static unsigned int load_rknn(const char *path, unsigned char *model,
                              rknn_context *ctx, rknn_input_output_num *io_num) {
    int ret;
    int model_len = 0;
    model = load_model(path, &model_len);
    ret = rknn_init(ctx, model, model_len, 0);
    if (ret < 0) {
        printf("rknn_init fail! ret=%d\n", ret);
        return -1;
    }

    ret = rknn_query(*ctx, RKNN_QUERY_IN_OUT_NUM, io_num, sizeof(*io_num));
    if (ret != RKNN_SUCC) {
        printf("rknn_query fail! ret=%d\n", ret);
        return -1;
    }
    printf("model input num: %d, output num: %d\n", io_num->n_input, io_num->n_output);

    return 0;
}

static unsigned int inference(const char* path, rknn_context *ctx, rknn_input_output_num *io_num) {
    // load image
    cv::Mat orig_img = imread(path, cv::IMREAD_COLOR);
    if (!orig_img.data) {
        printf("cv::imread %s fail!\n", path);
        return -1;
    }

    // pre-dataprocess
    cv::Mat img = orig_img.clone();
    if(orig_img.cols != kIMG_W || orig_img.rows != kIMG_H) {
        printf("resize %d %d to %d %d\n", orig_img.cols, orig_img.rows, kIMG_W, kIMG_H);
        cv::resize(orig_img, img, cv::Size(kIMG_W, kIMG_H), (0, 0), (0, 0), cv::INTER_LINEAR);
    }
    cv::cvtColor(img, img, COLOR_BGR2RGB);

    // Set Input Data
    rknn_input inputs[1];
    memset(inputs, 0, sizeof(inputs));
    inputs[0].index = 0;
    inputs[0].type = RKNN_TENSOR_UINT8;
    inputs[0].size = img.cols*img.rows*img.channels();
    inputs[0].fmt = RKNN_TENSOR_NHWC;
    inputs[0].buf = img.data;

    int ret;
    ret = rknn_inputs_set(*ctx, io_num->n_input, inputs);
    if(ret < 0) {
        printf("rknn_input_set fail! ret=%d\n", ret);
        return -1;
    }

    // Run
    printf("infer...\n");
    ret = rknn_run(*ctx, nullptr);
    if(ret < 0) {
        printf("rknn_run fail! ret=%d\n", ret);
        return -1;
    }

    // Get Output
    rknn_output outputs[1];
    memset(outputs, 0, sizeof(outputs));
    outputs[0].want_float = 1;
    ret = rknn_outputs_get(*ctx, 1, outputs, NULL);
    if(ret < 0) {
        printf("rknn_outputs_get fail! ret=%d\n", ret);
        return -1;
    }

/*
    // Post Process
    for (int i = 0; i < output_attrs[0].n_elems; i++) {
        float val = ((float*)(outputs[0].buf))[i];
        if (val > 0.01) {
            printf("%d - %f\n", i, val);
        }
    }
*/

    // release rknn_outputs
    rknn_outputs_release(*ctx, 1, outputs);
}

int main(int argc, char** argv) {

    rknn_context ctx;
    int model_len = 0;
    unsigned char *model;
    rknn_input_output_num io_num;

    int ret = load_rknn(argv[1], model, &ctx, &io_num);

    int fd_pipeo;
    if ((fd_pipeo = open(kPIPE_O_PATH, O_RDONLY)) < 0) {
        printf("fd_pipeo %s fail!\n", kPIPE_O_PATH);
        exit(ERRNO_BROKEN_PIPE);
    }

    int ret;
    char buf[BUFFERS_SIZE];
    while ((ret = read(fd_pipeo, buf, BUFFERS_SIZE)) > 0) {
        printf("%s\n", buf);
        switch (buf[0]) {
            case 'L':
                printf("load model!\n");
                break;
            case 'I':
                printf("inference!\n");
                break;
            case 'Q':
                printf("exit!\n");
                exit(0);
            default:
                printf("invalid operator!\n");
                break;
        }
    }

    // Release
    if(ctx >= 0) {
        rknn_destroy(ctx);
    }
    if(model) {
        free(model);
    }
    return 0;
}
