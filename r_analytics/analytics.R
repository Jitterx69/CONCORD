# CONCORD Quantum Analytics
# Analyzes the probability divergence of parallel World States

library(jsonlite)
library(ggplot2)

analyze_worlds <- function(json_data) {
  data <- fromJSON(json_data)
  
  # Calculate Probability Entropy
  metrics <- data.frame(
    world_id = data$id,
    probability = data$probability,
    entropy = -data$probability * log2(data$probability + 1e-9)
  )
  
  print("--- World State Analysis ---")
  print(metrics)
  
  total_entropy <- sum(metrics$entropy)
  print(paste("System Entropy:", total_entropy))
  
  if (total_entropy > 1.0) {
    print("ALERT: High Narrative Uncertainty detected!")
  }
}

plot_divergence <- function(data) {
  # Mock plotting logic for Divergence Graph
  p <- ggplot(data, aes(x=name, y=probability, fill=name)) +
    geom_bar(stat="identity") +
    theme_minimal() +
    labs(title="Quantum World Probabilities", x="Theory", y="Probability")
    
  ggsave("divergence_plot.png", p)
}

# Example Usage (when run via Rscript)
# args <- commandArgs(trailingOnly = TRUE)
# if (length(args) > 0) {
#   analyze_worlds(args[1])
# }
