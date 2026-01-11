# CONCORD Predictive Analytics
# Forecasts Future Consistency Trends using Linear Regression

library(jsonlite)
library(ggplot2)

forecast_trends <- function(json_path) {
  if (!file.exists(json_path)) {
    stop("Input file not found")
  }

  data <- fromJSON(json_path)
  
  # Mock data standardization if needed
  if (is.null(data$time_step)) data$time_step <- 1:nrow(data)
  if (is.null(data$score)) data$score <- runif(nrow(data), 0.5, 1.0)

  # Train Simple Linear Model
  model <- lm(score ~ time_step, data=data)
  
  # Predict next 5 steps
  future_steps <- data.frame(time_step = (max(data$time_step) + 1):(max(data$time_step) + 5))
  prediction <- predict(model, newdata=future_steps)
  
  future_data <- cbind(future_steps, score=prediction)
  combined_data <- rbind(data[,c("time_step", "score")], future_data)
  combined_data$type <- c(rep("Historical", nrow(data)), rep("Forecast", 5))

  print("--- Forecast for Next 5 Steps ---")
  print(future_data)

  p <- ggplot(combined_data, aes(x=time_step, y=score, color=type)) +
    geom_line(size=1.2) +
    geom_point() +
    theme_minimal() +
    labs(title="Consistency Trend Forecast", x="Narrative Step", y="Consistency Score")
    
  ggsave("forecast_plot.png", p)
  print("Forecast plot saved to forecast_plot.png")
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  forecast_trends(args[1])
}
