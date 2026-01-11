FROM maven:3.9-eclipse-temurin-17 as builder

WORKDIR /app
COPY java_services/pom.xml .
COPY java_services/src ./src

# Build
# Note: Since we don't assume a valid pom.xml exists in the user's files yet (I implemented source without pom), 
# I will create a simple compilation step instead of full maven build if pom is missing.
# But for a proper Dockerfile, let's assume standard javac for simplicity if pom is missing.

WORKDIR /app/src
RUN javac -d /app/classes main/java/com/concord/federation/*.java

FROM eclipse-temurin:17-jdk-jammy
WORKDIR /app
COPY --from=builder /app/classes .

# Run
CMD ["java", "com.concord.federation.FederationService"]
