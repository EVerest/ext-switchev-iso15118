/*
 * SPDX-License-Identifier: Apache-2.0
 * Copyright 2024 Contributors to EVerest
 *
 * cbv2g_json_wrapper.c - Main wrapper implementation
 */

#include "cbv2g_json_wrapper.h"
#include "converters.h"
#include <string.h>
#include <stdio.h>

/* Thread-local error message buffer */
static __thread char g_last_error[1024] = {0};

/* Internal function to set error message */
void set_error(const char* format, ...) {
    va_list args;
    va_start(args, format);
    vsnprintf(g_last_error, sizeof(g_last_error), format, args);
    va_end(args);
}

const char* cbv2g_get_version(void) {
    return CBV2G_JSON_WRAPPER_VERSION;
}

const char* cbv2g_get_last_error(void) {
    return g_last_error;
}

void cbv2g_clear_error(void) {
    g_last_error[0] = '\0';
}

/* Determine protocol from namespace */
typedef enum {
    PROTOCOL_UNKNOWN = 0,
    PROTOCOL_SAP,
    PROTOCOL_DIN,
    PROTOCOL_ISO2,
    PROTOCOL_ISO20_COMMON,
    PROTOCOL_ISO20_AC,
    PROTOCOL_ISO20_DC,
    PROTOCOL_ISO20_WPT,
    PROTOCOL_ISO20_ACDP
} protocol_t;

static protocol_t get_protocol(const char* namespace) {
    if (namespace == NULL) {
        return PROTOCOL_UNKNOWN;
    }

    if (strcmp(namespace, NS_SAP) == 0) {
        return PROTOCOL_SAP;
    }
    if (strcmp(namespace, NS_DIN_MSG_DEF) == 0) {
        return PROTOCOL_DIN;
    }
    if (strcmp(namespace, NS_ISO_V2_MSG_DEF) == 0) {
        return PROTOCOL_ISO2;
    }
    if (strcmp(namespace, NS_ISO_V20_COMMON_MSG) == 0) {
        return PROTOCOL_ISO20_COMMON;
    }
    if (strcmp(namespace, NS_ISO_V20_AC) == 0) {
        return PROTOCOL_ISO20_AC;
    }
    if (strcmp(namespace, NS_ISO_V20_DC) == 0) {
        return PROTOCOL_ISO20_DC;
    }
    if (strcmp(namespace, NS_ISO_V20_WPT) == 0) {
        return PROTOCOL_ISO20_WPT;
    }
    if (strcmp(namespace, NS_ISO_V20_ACDP) == 0) {
        return PROTOCOL_ISO20_ACDP;
    }
    /* Check for ISO20 base prefix */
    if (strncmp(namespace, NS_ISO_V20_BASE, strlen(NS_ISO_V20_BASE)) == 0) {
        return PROTOCOL_ISO20_COMMON;
    }

    return PROTOCOL_UNKNOWN;
}

int cbv2g_encode(const char* json_message,
                 const char* namespace,
                 uint8_t* output_buffer,
                 size_t buffer_size,
                 size_t* output_length) {

    /* Validate parameters */
    if (json_message == NULL || namespace == NULL ||
        output_buffer == NULL || output_length == NULL) {
        set_error("Invalid parameter: NULL pointer");
        return CBV2G_ERROR_INVALID_PARAM;
    }

    if (buffer_size == 0) {
        set_error("Invalid parameter: buffer_size is 0");
        return CBV2G_ERROR_INVALID_PARAM;
    }

    cbv2g_clear_error();

    /* Route to appropriate protocol encoder */
    protocol_t protocol = get_protocol(namespace);

    switch (protocol) {
        case PROTOCOL_SAP:
            return apphand_encode(json_message, output_buffer, buffer_size, output_length);

        /*
         * DIN, ISO-2, and ISO-20 converters will be added in subsequent PRs.
         * For now, these namespaces are recognized but not yet supported.
         */
        case PROTOCOL_DIN:
        case PROTOCOL_ISO2:
        case PROTOCOL_ISO20_COMMON:
        case PROTOCOL_ISO20_AC:
        case PROTOCOL_ISO20_DC:
        case PROTOCOL_ISO20_WPT:
        case PROTOCOL_ISO20_ACDP:
            set_error("Protocol not yet supported: %s", namespace);
            return CBV2G_ERROR_UNKNOWN_NAMESPACE;

        default:
            set_error("Unknown namespace: %s", namespace);
            return CBV2G_ERROR_UNKNOWN_NAMESPACE;
    }
}

int cbv2g_decode(const uint8_t* exi_data,
                 size_t exi_length,
                 const char* namespace,
                 char* output_json,
                 size_t buffer_size) {

    /* Validate parameters */
    if (exi_data == NULL || namespace == NULL || output_json == NULL) {
        set_error("Invalid parameter: NULL pointer");
        return CBV2G_ERROR_INVALID_PARAM;
    }

    if (exi_length == 0 || buffer_size == 0) {
        set_error("Invalid parameter: length is 0");
        return CBV2G_ERROR_INVALID_PARAM;
    }

    cbv2g_clear_error();

    /* Route to appropriate protocol decoder */
    protocol_t protocol = get_protocol(namespace);

    switch (protocol) {
        case PROTOCOL_SAP:
            return apphand_decode(exi_data, exi_length, output_json, buffer_size);

        /*
         * DIN, ISO-2, and ISO-20 converters will be added in subsequent PRs.
         * For now, these namespaces are recognized but not yet supported.
         */
        case PROTOCOL_DIN:
        case PROTOCOL_ISO2:
        case PROTOCOL_ISO20_COMMON:
        case PROTOCOL_ISO20_AC:
        case PROTOCOL_ISO20_DC:
        case PROTOCOL_ISO20_WPT:
        case PROTOCOL_ISO20_ACDP:
            set_error("Protocol not yet supported: %s", namespace);
            return CBV2G_ERROR_UNKNOWN_NAMESPACE;

        default:
            set_error("Unknown namespace: %s", namespace);
            return CBV2G_ERROR_UNKNOWN_NAMESPACE;
    }
}
