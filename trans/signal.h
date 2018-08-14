#ifndef SIGNAL_H
#define SIGNAL_H

/**
 * Signals between transmitter and receiver.
 * See spec/ for more details.
 * @author Joseph Rubin
 */

// We are ready for requests.
#define SIG_READY   "\x24\x25\x26"

// A capture is requested.
#define SIG_REQUEST '\x3C'
// The receiver is done with the capture.
#define SIG_ENOUGH  '\x3E'

// We mark the start of a capture.
#define SIG_HEAD    '\x22'
// We deny a SIG_REQUEST.
#define SIG_DENIED  '\x21'

#endif /* SIGNAL_H */

