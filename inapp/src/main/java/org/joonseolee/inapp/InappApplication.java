package org.joonseolee.inapp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class InappApplication {

  /**
   * Bootstraps and starts the Spring Boot application using this class as the primary configuration.
   *
   * @param args command-line arguments passed to the application
   */
  public static void main(String[] args) {
    SpringApplication.run(InappApplication.class, args);
  }
}