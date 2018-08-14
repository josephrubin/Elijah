#ifndef METRIC_H
#define METRIC_H

/**
 * Constants for measuring various metrics in demo mode.
 * @author Joseph Rubin
 */

// Average magnitude metric does not consider values below this threshold.
#define MAGNITUDE_THRESHOLD 3

// Peaks are at least this high.
// Blindspots only consider values less than this threshold.
#define PEAK_MAGNITUDE_THRESHOLD 25
// Peaks must fall by this much in a single frame to be considered peaks.
#define PEAK_MAGNITUDE_CHANGE_THRESHOLD 4
// Peaks that are this far away are not coonsidered connected.
// That is, we do not factor in their distance to see how far peaks generally are from each other.
#define PEAK_DISTANCE_MAX 150

// If a blindspot is shorter than this, we don't count it.
#define BLINDSPOT_DURATION_MIN 70

#endif /* METRIC_H */
