/* MC1 board adaptation, separate from Silicon Labs vendor sources.
 * Seeed XIAO MG24 schematic v1.1, sheet 05 EFR32MG24B220:
 * PB05 powers FM8625H; PB04=0 selects RF1 (onboard ceramic), 1 = RF2/U.FL.
 */
#ifndef MC1_BOARD_INIT_H
#define MC1_BOARD_INIT_H

#include "em_gpio.h"
#include "mc1_antenna_config.h"

#if !defined(MC1_ANTENNA_EXTERNAL) || (MC1_ANTENNA_EXTERNAL != 0 && MC1_ANTENNA_EXTERNAL != 1)
#error "Generate an explicit onboard/external XIAO antenna configuration"
#endif

static inline void mc1_xiao_board_init(void)
{
  /* Called immediately after sl_gpio_init(), before sl_stack_init(). */
  GPIO_PinModeSet(gpioPortB, 4, gpioModePushPull, MC1_ANTENNA_EXTERNAL);
  GPIO_PinModeSet(gpioPortB, 5, gpioModePushPull, 1);
  /* Keep unused onboard SPI flash deselected and the active-low LED off. */
  GPIO_PinModeSet(gpioPortA, 6, gpioModePushPull, 1);
  GPIO_PinModeSet(gpioPortA, 7, gpioModePushPull, 1);
}

#endif
