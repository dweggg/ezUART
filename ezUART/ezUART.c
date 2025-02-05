#include "ezUART.h"
#define MAX_VARS 10   // Maximum number of variables you want to send
#define VAR_SIZE 4    // Size of each variable (4 bytes)

uint32_t vars[MAX_VARS];  // Array to hold the 4-byte variables

void send_ezUART(void *var, int id) {
    // Ensure the id is within bounds
    if (id < 0 || id >= MAX_VARS) {
        return;  // Invalid ID, do nothing
    }

    // Check the type of the variable and store it as a 4-byte value
    if (sizeof(var) > VAR_SIZE) {
        // Trim larger types to 4 bytes (e.g., long long)
        memcpy(&vars[id], var, VAR_SIZE);
    } else if (sizeof(var) == VAR_SIZE) {
        // Copy directly if it's already 4 bytes (e.g., int, float)
        memcpy(&vars[id], var, VAR_SIZE);
    }
    // If the variable is smaller, you would need to zero-extend it,
    // but for now, we assume only 4-byte data.
}