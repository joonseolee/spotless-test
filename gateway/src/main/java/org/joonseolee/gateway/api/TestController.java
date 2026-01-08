package org.joonseolee.gateway.api;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/test")
public class TestController {

  @GetMapping
  public Object sayHello() {
    // 아무것도 아닌것도 만들어야지
    int nonValue = 0;
    return Map.of("sentence", "hello world!");
  }
}
