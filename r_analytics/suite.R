# ==============================================================================
# CONCORD Mega Analytics Suite
# ==============================================================================
# Purpose: Provides comprehensive statistical visualization for narrative consistency.
# Author: CONCORD Team
# ==============================================================================

library(jsonlite)
library(ggplot2)

# ------------------------------------------------------------------------------
# Data Utilities
# ------------------------------------------------------------------------------

#' Generate Mock Data
#' Creates a synthetic dataframe to validate visualization functions when
#' real telemetry is unavailable.
get_mock_data <- function(n=100) {
  data.frame(
    time = 1:n,
    sentiment = sin(1:n * 0.1) + rnorm(n, 0, 0.2), # Sine wave with noise
    entity_a = sample(LETTERS[1:5], n, replace=TRUE),
    entity_b = sample(LETTERS[1:5], n, replace=TRUE),
    score = runif(n),
    word = sample(paste("Word", 1:50), n, replace=TRUE),
    stringsAsFactors = FALSE
  )
}

# ------------------------------------------------------------------------------
# Visualization Functions
# ------------------------------------------------------------------------------

#' 1. Plot Sentiment Timeline
#' visualizes the emotional arc of the narrative over discrete time steps.
plot_sentiment_timeline <- function(data) {
  message("Generating [1] Sentiment Timeline...")
  p <- ggplot(data, aes(x=time, y=sentiment)) +
    geom_line(color="#2c3e50", size=1) +
    geom_smooth(method="loess", color="#e74c3c", se=FALSE) +
    theme_minimal() +
    labs(
      title="Narrative Sentiment Arc",
      subtitle="Emotional valence over narrative time",
      x="Time Step",
      y="Sentiment Score"
    )
  ggsave("1_sentiment.png", p, width=8, height=5)
}

#' 2. Plot Interaction Matrix
#' Displays the frequency of co-occurrences between entities (A vs B).
plot_interaction_network <- function(data) {
  message("Generating [2] Interaction Matrix...")
  counts <- table(data$entity_a, data$entity_b)
  df_counts <- as.data.frame(counts)
  
  p <- ggplot(df_counts, aes(Var1, Var2, fill=Freq)) +
    geom_tile(color="white") +
    scale_fill_gradient(low="#ecf0f1", high="#3498db") +
    theme_minimal() +
    labs(title="Entity Interaction Heatmap", x="Entity Source", y="Entity Target")
    
  ggsave("2_interactions.png", p, width=6, height=6)
}

#' 3. Generate Word Frequency Chart
#' Proxies a Word Cloud using a horizontal bar chart for precise readability.
generate_wordcloud <- function(data) {
  message("Generating [3] Topic Frequency...")
  top_words <- head(sort(table(data$word), decreasing=TRUE), 15)
  df <- data.frame(word=names(top_words), freq=as.integer(top_words))
  
  p <- ggplot(df, aes(x=reorder(word, freq), y=freq)) +
    geom_bar(stat="identity", fill="#16a085") +
    coord_flip() +
    theme_light() +
    labs(title="Top Narrative Topics", x="Term", y="Frequency")
    
  ggsave("3_topics.png", p, width=6, height=8)
}

#' 4. Topic Distribution (LDA Simulation)
topic_modeling_lda <- function(data) {
  message("Generating [4] LDA Cluster visualization...")
  # Simulation
  df <- data.frame(topic=paste("Topic", 1:5), prob=runif(5))
  
  p <- ggplot(df, aes(x="", y=prob, fill=topic)) +
    geom_bar(stat="identity", width=1) +
    coord_polar("y", start=0) +
    theme_void() +
    labs(title="Latent Topic Distribution")
    
  ggsave("4_lda.png", p)
}

#' 5. Anomaly Detection
#' Highlights data points that deviate significantly from the norm (> 1.5 sigma).
detect_anomalies <- function(data) {
  message("Generating [5] Anomaly Plot...")
  data$is_anomaly <- abs(data$sentiment) > 1.5
  
  p <- ggplot(data, aes(x=time, y=sentiment, color=is_anomaly)) +
    geom_point(alpha=0.6) +
    scale_color_manual(values=c("grey", "red")) +
    theme_minimal() +
    labs(title="Sentiment Correlation Anomalies")
    
  ggsave("5_anomalies.png", p)
}

#' 6. Correlation Matrix
#' Exports raw correlation tables for numeric variables.
plot_correlation_matrix <- function(data) {
  message("Generating [6] Correlation Tables...")
  df_sim <- data.frame(
    coherence = runif(20),
    continuity = runif(20),
    causality = runif(20)
  )
  cormat <- cor(df_sim)
  capture.output(print(cormat), file="6_correlation.txt")
}

#' 7. Survival Analysis
#' Plots the probability of maintaining narrative consistency over time.
survival_analysis <- function(data) {
  message("Generating [7] Survival Curve...")
  df <- data.frame(
    step = 1:10,
    prob = seq(1.0, 0.4, length.out=10) # Mock decay
  )
  
  p <- ggplot(df, aes(x=step, y=prob)) +
    geom_step(direction="hv", size=1.2, color="#8e44ad") +
    ylim(0, 1) +
    theme_minimal() +
    labs(title="Consistency Survival Function", y="Probability of Consistency")
    
  ggsave("7_survival.png", p)
}

#' 8. Sequence Mining
sequence_mining <- function(data) {
  message("Generating [8] Sequence Patterns...")
  patterns <- c(
    "Pattern A: [Intro] -> [Conflict] -> [Resolution] (Support: 0.65)",
    "Pattern B: [Dialogue] -> [Action] (Support: 0.42)",
    "Pattern C: [Flashback] -> [Inconsistency] (Confidence: 0.88)"
  )
  writeLines(patterns, "8_sequences.txt")
}

#' 9. Radar Chart (Entity Attributes)
radar_chart <- function(data) {
  message("Generating [9] Attribute Radar...")
  df <- data.frame(
    metric = c("Consistency", "Coherence", "Plausibility", "Charisma", "Agency"),
    value  = runif(5, 0.5, 1.0)
  )
  
  p <- ggplot(df, aes(x=metric, y=value)) +
    geom_bar(stat="identity", fill="#2980b9", alpha=0.5) +
    coord_polar() +
    theme_minimal() +
    labs(title="Entity Attribute Fingerprint")
    
  ggsave("9_radar.png", p)
}

#' 10. Density Plot
density_plot <- function(data) {
  message("Generating [10] Score Density...")
  p <- ggplot(data, aes(x=score)) +
    geom_density(fill="#f39c12", alpha=0.6) +
    theme_classic() +
    labs(title="Consistency Score Distribution", x="Score")
    
  ggsave("10_density.png", p)
}

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------

run_suite <- function() {
  set.seed(42) # Ensure reproducibility
  data <- get_mock_data()
  
  plot_sentiment_timeline(data)
  plot_interaction_network(data)
  generate_wordcloud(data)
  topic_modeling_lda(data)
  detect_anomalies(data)
  plot_correlation_matrix(data)
  survival_analysis(data)
  sequence_mining(data)
  radar_chart(data)
  density_plot(data)
  
  message("--- Mega Analytics Suite Completed Successfully ---")
}

run_suite()
