#!/usr/bin/env Rscript
# predict.R
# Args: <csv_path> <mapping_json_path> <chart_output_dir> <target_field> <periods>
#
# target_field is a STANDARD field name (e.g. "sales", "quantity", "profit"),
# looked up via the mapping to find the real column. If a date column is
# mapped and there's enough history, forecasts with auto.arima (falls back
# to ets, then to a plain linear trend if forecast/lubridate can't be used
# or there isn't enough data for a seasonal model).

suppressMessages({
  library(jsonlite)
  library(dplyr)
  library(lubridate)
  library(ggplot2)
  library(scales)
  ok_forecast <- requireNamespace("forecast", quietly = TRUE)
  if (ok_forecast) library(forecast)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 5) {
  stop("Usage: predict.R <csv_path> <mapping_json_path> <chart_output_dir> <target_field> <periods>")
}
csv_path     <- args[1]
mapping_path <- args[2]
chart_dir    <- args[3]
target_field <- args[4]
periods      <- as.integer(args[5])

dir.create(chart_dir, showWarnings = FALSE, recursive = TRUE)

mapping <- fromJSON(mapping_path)
df <- read.csv(csv_path, stringsAsFactors = FALSE, check.names = FALSE)

if (is.null(mapping[[target_field]]) || !nzchar(mapping[[target_field]]) ||
    !(mapping[[target_field]] %in% names(df))) {
  cat(toJSON(list(status = "error",
                   message = paste0("No column mapped for target field '", target_field, "'.")),
             auto_unbox = TRUE))
  quit(status = 0)
}

target_col <- mapping[[target_field]]
df[[target_col]] <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", df[[target_col]])))

has_date <- !is.null(mapping$date) && nzchar(mapping$date) && mapping$date %in% names(df)

method_used <- NULL
forecast_points <- list()
history_points <- list()
warnings_out <- c()

if (has_date) {
  parsed <- suppressWarnings(parse_date_time(df[[mapping$date]],
              orders = c("ymd","mdy","dmy","ymd HMS","mdy HMS","dmy HMS")))
  df$.__date <- as.Date(parsed)
  df <- df %>% filter(!is.na(.__date), !is.na(.data[[target_col]]))
}

if (has_date && nrow(df) >= 8) {
  daily <- df %>%
    group_by(.__date) %>%
    summarise(value = sum(.data[[target_col]], na.rm = TRUE), .groups = "drop") %>%
    arrange(.__date)

  span_days <- as.numeric(max(daily$.__date) - min(daily$.__date))

  if (span_days >= 60) {
    # aggregate monthly if we span a couple months+, else keep daily
    series_df <- daily %>%
      mutate(period = floor_date(.__date, "month")) %>%
      group_by(period) %>%
      summarise(value = sum(value), .groups = "drop") %>%
      arrange(period)
    freq <- 12
    period_unit <- "month"
  } else {
    series_df <- daily %>% rename(period = .__date)
    freq <- 7
    period_unit <- "day"
  }

  n_obs <- nrow(series_df)

  if (ok_forecast && n_obs >= max(8, freq + 1)) {
    ts_data <- ts(series_df$value, frequency = min(freq, n_obs))
    fit <- tryCatch(auto.arima(ts_data), error = function(e) NULL)
    if (is.null(fit)) fit <- tryCatch(ets(ts_data), error = function(e) NULL)
    if (!is.null(fit)) {
      fc <- forecast(fit, h = periods)
      method_used <- paste0("auto.arima/ets on ", period_unit, "ly totals")

      last_period <- max(series_df$period)
      step <- if (period_unit == "month") months(1) else days(1)
      future_periods <- last_period + step * (1:periods)

      history_points <- setNames(as.list(round(series_df$value, 2)), as.character(series_df$period))
      forecast_points <- setNames(as.list(round(as.numeric(fc$mean), 2)), as.character(future_periods))

      plot_df <- rbind(
        data.frame(period = series_df$period, value = series_df$value, type = "actual"),
        data.frame(period = future_periods, value = as.numeric(fc$mean), type = "forecast")
      )
      ci_df <- data.frame(period = future_periods, lo = as.numeric(fc$lower[,2]), hi = as.numeric(fc$upper[,2]))

      p <- ggplot() +
        geom_ribbon(data = ci_df, aes(x = period, ymin = lo, ymax = hi), fill = "#F2A541", alpha = 0.25) +
        geom_line(data = plot_df, aes(x = period, y = value, color = type, linetype = type), linewidth = 1.1) +
        geom_point(data = plot_df, aes(x = period, y = value, color = type), size = 1.8) +
        scale_color_manual(values = c(actual = "#2C6E91", forecast = "#E76F51")) +
        scale_y_continuous(labels = comma) +
        labs(title = paste0("Forecast: ", target_field, " (next ", periods, " ", period_unit, "s)"),
             x = NULL, y = target_field, color = NULL, linetype = NULL) +
        theme_minimal(base_size = 13) +
        theme(plot.title = element_text(face = "bold", size = 15), legend.position = "top")

      chart_file <- file.path(chart_dir, "forecast.png")
      ggsave(chart_file, p, width = 9, height = 5, dpi = 130, bg = "white")
    }
  }

  if (is.null(method_used)) {
    # fallback: linear trend on the aggregated series
    series_df$idx <- seq_len(nrow(series_df))
    lm_fit <- lm(value ~ idx, data = series_df)
    future_idx <- (max(series_df$idx) + 1):(max(series_df$idx) + periods)
    preds <- predict(lm_fit, newdata = data.frame(idx = future_idx))
    method_used <- paste0("linear trend on ", period_unit, "ly totals (fallback)")
    warnings_out <- c(warnings_out, "Dataset too short/irregular for ARIMA — used a simple linear trend instead.")

    step <- if (period_unit == "month") months(1) else days(1)
    last_period <- max(series_df$period)
    future_periods <- last_period + step * (1:periods)

    history_points <- setNames(as.list(round(series_df$value, 2)), as.character(series_df$period))
    forecast_points <- setNames(as.list(round(as.numeric(preds), 2)), as.character(future_periods))

    plot_df <- rbind(
      data.frame(period = series_df$period, value = series_df$value, type = "actual"),
      data.frame(period = future_periods, value = as.numeric(preds), type = "forecast")
    )
    p <- ggplot(plot_df, aes(x = period, y = value, color = type, linetype = type)) +
      geom_line(linewidth = 1.1) + geom_point(size = 1.8) +
      scale_color_manual(values = c(actual = "#2C6E91", forecast = "#E76F51")) +
      scale_y_continuous(labels = comma) +
      labs(title = paste0("Forecast: ", target_field, " (next ", periods, " ", period_unit, "s)"),
           x = NULL, y = target_field, color = NULL, linetype = NULL) +
      theme_minimal(base_size = 13) +
      theme(plot.title = element_text(face = "bold", size = 15), legend.position = "top")
    ggsave(file.path(chart_dir, "forecast.png"), p, width = 9, height = 5, dpi = 130, bg = "white")
  }

} else {
  # no usable date column — predict next N row-index values via linear trend
  vals <- df[[target_col]]
  vals <- vals[!is.na(vals)]
  if (length(vals) < 5) {
    cat(toJSON(list(status = "error", message = "Not enough valid numeric data to predict."),
               auto_unbox = TRUE))
    quit(status = 0)
  }
  idx <- seq_along(vals)
  lm_fit <- lm(vals ~ idx)
  future_idx <- (length(vals) + 1):(length(vals) + periods)
  preds <- predict(lm_fit, newdata = data.frame(idx = future_idx))
  method_used <- "linear trend on row order (no date column mapped)"
  warnings_out <- c(warnings_out, "No date column mapped — forecast is based on row order, not real time.")

  history_points <- setNames(as.list(round(vals, 2)), as.character(idx))
  forecast_points <- setNames(as.list(round(as.numeric(preds), 2)), as.character(future_idx))

  plot_df <- rbind(
    data.frame(x = idx, value = vals, type = "actual"),
    data.frame(x = future_idx, value = as.numeric(preds), type = "forecast")
  )
  p <- ggplot(plot_df, aes(x = x, y = value, color = type, linetype = type)) +
    geom_line(linewidth = 1.1) + geom_point(size = 1.8) +
    scale_color_manual(values = c(actual = "#2C6E91", forecast = "#E76F51")) +
    scale_y_continuous(labels = comma) +
    labs(title = paste0("Forecast: ", target_field, " (next ", periods, " rows)"),
         x = "Row order", y = target_field, color = NULL, linetype = NULL) +
    theme_minimal(base_size = 13) +
    theme(plot.title = element_text(face = "bold", size = 15), legend.position = "top")
  ggsave(file.path(chart_dir, "forecast.png"), p, width = 9, height = 5, dpi = 130, bg = "white")
}

output <- list(
  status = "ok",
  target = target_field,
  method = method_used,
  periods_requested = periods,
  history = history_points,
  forecast = forecast_points,
  chart = "forecast.png",
  warnings = as.list(warnings_out)
)

cat(toJSON(output, auto_unbox = TRUE, na = "null", digits = 4))
