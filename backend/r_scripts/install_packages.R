# Run once: Rscript install_packages.R
pkgs <- c("jsonlite", "dplyr", "ggplot2", "lubridate", "scales", "forecast")
to_install <- pkgs[!(pkgs %in% installed.packages()[, "Package"])]
if (length(to_install)) install.packages(to_install, repos = "https://cloud.r-project.org")
cat("All required R packages are installed.\n")
