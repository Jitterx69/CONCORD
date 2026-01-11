FROM r-base:latest

WORKDIR /app

# Install R dependencies
RUN R -e "install.packages(c('jsonlite', 'ggplot2'), repos='http://cran.rstudio.com/')"

COPY r_analytics /app/r_analytics

# Expose port (if plumbing API)
# EXPOSE 8000

# Run script wrapper
# CMD ["Rscript", "r_analytics/analytics.R"]
CMD ["tail", "-f", "/dev/null"]
