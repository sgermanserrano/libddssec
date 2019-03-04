/*
 * DDS Security library
 * Copyright (c) 2018-2019, Arm Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <dsec_macros.h>
#include <tee_ta_api.h>
#include <trace.h>

TEE_Result TA_CreateEntryPoint(void)
{
    DMSG("Creating libddssec's TA");
    return TEE_SUCCESS;
}

void TA_DestroyEntryPoint(void)
{
    DMSG("Destroying libddssec's TA");
}

TEE_Result TA_OpenSessionEntryPoint(uint32_t ptype,
                                    TEE_Param param[TEE_NUM_PARAMS],
                                    void** session_id_ptr)
{
    DSEC_UNUSED(ptype);
    DSEC_UNUSED(param);
    DSEC_UNUSED(session_id_ptr);

    return TEE_SUCCESS;
}

void TA_CloseSessionEntryPoint(void* sess_ptr)
{
    DSEC_UNUSED(sess_ptr);
}

TEE_Result TA_InvokeCommandEntryPoint(void* session_id,
                                      uint32_t command_id,
                                      uint32_t parameters_type,
                                      TEE_Param parameters[TEE_NUM_PARAMS])
{
    TEE_Result result = 0;
    DSEC_UNUSED(session_id);
    DSEC_UNUSED(parameters_type);
    DSEC_UNUSED(parameters);

    switch (command_id) {

#if DSEC_TEST
#endif /* DSEC_TEST */
    default:
        DMSG("Invalid command identifier");
        result = TEE_ERROR_BAD_PARAMETERS;
        break;
    }

    return result;
}
