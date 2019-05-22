/*
 * DDS Security library
 * Copyright (c) 2019, Arm Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <dsec_ssh.h>
#include <dsec_ca.h>
#include <dsec_errno.h>
#include <dsec_print.h>
#include <dsec_ta.h>

int32_t dsec_ssh_derive(int32_t* ssh_id,
                        const struct dsec_instance* instance,
                        int32_t hh_id)
{

    TEEC_Result teec_result = 0;
    int32_t result = 0;
    uint32_t return_origin = 0;
    TEEC_Operation operation = {0};

    if (ssh_id != NULL) {
        operation.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_OUTPUT,
                                                TEEC_VALUE_INPUT,
                                                TEEC_NONE,
                                                TEEC_NONE);

        operation.params[1].value.a = (uint32_t)hh_id;

        teec_result = dsec_ca_invoke(instance,
                                     DSEC_TA_CMD_SSH_DERIVE,
                                     &operation,
                                     &return_origin);

        result = dsec_ca_convert_teec_result(teec_result);
        if (teec_result == DSEC_SUCCESS) {
            *ssh_id = operation.params[0].value.a;
        } else {
            *ssh_id = -1;
            (void)dsec_print("An error occurred: TEEC_Result=0x%x, "
                             "DSEC_E=0x%x\n",
                             teec_result,
                             result);
        }
    } else {
        result = DSEC_E_PARAM;
        (void)dsec_print("Given parameter is NULL.\n");
    }

    return result;
}
