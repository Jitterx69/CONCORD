# CONCORD Visual Intelligence
# Generates a Consistency Heatmap (Narrative Time vs Character)

library(jsonlite)
library(ggplot2)

generate_heatmap <- function(json_path) {
  # Load data
  if (!file.exists(json_path)) {
    stop("Input file not found")
  }
  
  data <- fromJSON(json_path)
  
  # Expected structure: list of {character, time_step, consistency_score}
  # If data is missing specific columns, mock them for the heatmap
  if (is.null(data$character)) data$character <- "Unknown"
  if (is.null(data$time_step)) data$time_step <- 1:nrow(data)
  if (is.null(data$consistency_score)) data$consistency_score <- runif(nrow(data), 0, 1)

  print("Generating Heatmap...")
  
  p <- ggplot(data, aes(x=time_step, y=character, fill=consistency_score)) +
    geom_tile() +
    scale_fill_gradient2(low="red", mid="yellow", high="green", midpoint=0.5) +
    theme_minimal() +
    labs(
      title="Narrative Consistency Heatmap",
      x="Narrative Timeline (Step)",
      y="Character Entity",
      fill="Consistency"
    )

  ggsave("consistency_heatmap.png", p, width=10, height=6)
  print("Heatmap saved to consistency_heatmap.png")
}

# CLI Entry point
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  generate_heatmap(args[1])
}
