package org.joonseolee.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class GatewayApplication {

  /**
   * Application entry point that launches the Spring Boot application.
   *
   * @param args command-line arguments forwarded to SpringApplication
   */
  public static void main(String[] args) {
    SpringApplication.run(GatewayApplication.class, args);
  }
}