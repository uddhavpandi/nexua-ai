#!/usr/bin/env Rscript
# analyze.R
# Args: <csv_path> <mapping_json_path> <chart_output_dir>
#
# Reads the uploaded dataset + the standard-field -> raw-column mapping
# (produced by the Python backend's hash-map detector, possibly edited
# by the user), runs whatever business analyses the available columns
# support, saves charts as PNGs into chart_output_dir, and prints ONE
# JSON object to stdout (the last line) describing what was computed.

suppressMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
  library(lubridate)
  library(scales)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: analyze.R <csv_path> <mapping_json_path> <chart_output_dir>")
}
csv_path    <- args[1]
mapping_path<- args[2]
chart_dir   <- args[3]

dir.create(chart_dir, showWarnings = FALSE, recursive = TRUE)

mapping <- fromJSON(mapping_path)
df <- read.csv(csv_path, stringsAsFactors = FALSE, check.names = FALSE)

has <- function(field) !is.null(mapping[[field]]) && nzchar(mapping[[field]]) && mapping[[field]] %in% names(df)
col <- function(field) df[[mapping[[field]]]]

theme_biz <- theme_minimal(base_size = 13) +
  theme(
    plot.title = element_text(face = "bold", size = 15),
    panel.grid.minor = element_blank(),
    axis.title = element_text(color = "grey30")
  )
palette_biz <- c("#2C6E91", "#5FA8D3", "#F2A541", "#E76F51", "#6B9080", "#9381FF")

charts <- list()
summary_stats <- list()
breakdowns <- list()
warnings_out <- c()

# ---- coerce numeric / date columns where mapped -----------------------
if (has("sales"))    df[[mapping$sales]]    <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", col("sales"))))
if (has("quantity")) df[[mapping$quantity]] <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", col("quantity"))))
if (has("profit"))   df[[mapping$profit]]   <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", col("profit"))))
if (has("price"))    df[[mapping$price]]    <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", col("price"))))

if (has("date")) {
  parsed <- suppressWarnings(parse_date_time(col("date"),
              orders = c("ymd","mdy","dmy","ymd HMS","mdy HMS","dmy HMS")))
  df[[mapping$date]] <- as.Date(parsed)
  if (all(is.na(df[[mapping$date]]))) {
    warnings_out <- c(warnings_out, "Date column could not be parsed; time trends skipped.")
  }
}

# ---- overall summary ----------------------------------------------------
summary_stats$row_count <- nrow(df)
if (has("sales")) {
  s <- col("sales")
  summary_stats$total_sales  <- round(sum(s, na.rm = TRUE), 2)
  summary_stats$average_sale <- round(mean(s, na.rm = TRUE), 2)
  summary_stats$median_sale  <- round(median(s, na.rm = TRUE), 2)
  summary_stats$max_sale     <- round(max(s, na.rm = TRUE), 2)
}
if (has("quantity")) {
  summary_stats$total_units_sold <- sum(col("quantity"), na.rm = TRUE)
}
if (has("profit")) {
  p <- col("profit")
  summary_stats$total_profit <- round(sum(p, na.rm = TRUE), 2)
  if (has("sales")) {
    total_sales_val <- sum(col("sales"), na.rm = TRUE)
    if (total_sales_val != 0) {
      summary_stats$profit_margin_pct <- round(100 * sum(p, na.rm = TRUE) / total_sales_val, 2)
    }
  }
}
if (has("customer")) {
  summary_stats$unique_customers <- length(unique(col("customer")))
}

save_chart <- function(plot, name, width = 8, height = 5) {
  file <- file.path(chart_dir, paste0(name, ".png"))
  ggsave(file, plot, width = width, height = height, dpi = 130, bg = "white")
  charts[[name]] <<- basename(file)
}

# ---- sales trend over time (monthly) ------------------------------------
if (has("date") && has("sales") && !all(is.na(df[[mapping$date]]))) {
  trend <- df %>%
    filter(!is.na(.data[[mapping$date]])) %>%
    mutate(month = floor_date(.data[[mapping$date]], "month")) %>%
    group_by(month) %>%
    summarise(total = sum(.data[[mapping$sales]], na.rm = TRUE), .groups = "drop") %>%
    arrange(month)

  p <- ggplot(trend, aes(x = month, y = total)) +
    geom_line(color = palette_biz[1], linewidth = 1.1) +
    geom_point(color = palette_biz[1], size = 2) +
    scale_y_continuous(labels = comma) +
    labs(title = "Sales Trend Over Time", x = NULL, y = "Total Sales") +
    theme_biz
  save_chart(p, "sales_trend")

  breakdowns$monthly_sales <- trend %>%
    mutate(month = as.character(month)) %>%
    as.list() %>% lapply(as.list) %>%
    { setNames(as.list(trend$total), as.character(trend$month)) }
}

# ---- top N by a categorical dimension (product / category / region) ----
make_top_n_chart <- function(field, label, n = 10) {
  if (!has(field) || !has("sales")) return(invisible(NULL))
  agg <- df %>%
    group_by(.data[[mapping[[field]]]]) %>%
    summarise(total = sum(.data[[mapping$sales]], na.rm = TRUE), .groups = "drop") %>%
    arrange(desc(total)) %>%
    slice_head(n = n)
  names(agg)[1] <- "group"
  agg <- agg %>% filter(!is.na(group), group != "")

  if (nrow(agg) == 0) return(invisible(NULL))

  p <- ggplot(agg, aes(x = reorder(group, total), y = total)) +
    geom_col(fill = palette_biz[2]) +
    coord_flip() +
    scale_y_continuous(labels = comma) +
    labs(title = paste("Top", nrow(agg), label, "by Sales"), x = NULL, y = "Total Sales") +
    theme_biz
  save_chart(p, paste0("top_", field))

  breakdowns[[paste0("top_", field)]] <<- setNames(as.list(round(agg$total, 2)), as.character(agg$group))
}
make_top_n_chart("product", "Products")
make_top_n_chart("category", "Categories")
make_top_n_chart("region", "Regions")

# ---- category share (pie-style, done as bar since pies are hard to read)
if (has("category") && has("sales")) {
  share <- df %>%
    group_by(.data[[mapping$category]]) %>%
    summarise(total = sum(.data[[mapping$sales]], na.rm = TRUE), .groups = "drop") %>%
    filter(!is.na(.data[[mapping$category]]), .data[[mapping$category]] != "") %>%
    mutate(pct = round(100 * total / sum(total), 1))
  names(share)[1] <- "group"

  p <- ggplot(share, aes(x = "", y = total, fill = reorder(group, total))) +
    geom_col(width = 1) +
    coord_polar(theta = "y") +
    scale_fill_manual(values = rep(palette_biz, length.out = nrow(share))) +
    labs(title = "Sales Share by Category", fill = NULL, x = NULL, y = NULL) +
    theme_void(base_size = 13) +
    theme(plot.title = element_text(face = "bold", size = 15, hjust = 0.5))
  save_chart(p, "category_share")
}

# ---- sales distribution histogram ---------------------------------------
if (has("sales")) {
  p <- ggplot(df, aes(x = .data[[mapping$sales]])) +
    geom_histogram(bins = 30, fill = palette_biz[3], color = "white") +
    scale_x_continuous(labels = comma) +
    labs(title = "Sales Value Distribution", x = "Sale Amount", y = "Frequency") +
    theme_biz
  save_chart(p, "sales_distribution")
}

output <- list(
  status = "ok",
  summary = summary_stats,
  breakdowns = breakdowns,
  charts = charts,
  warnings = as.list(warnings_out),
  columns_used = mapping
)

cat(toJSON(output, auto_unbox = TRUE, na = "null", digits = 4))
