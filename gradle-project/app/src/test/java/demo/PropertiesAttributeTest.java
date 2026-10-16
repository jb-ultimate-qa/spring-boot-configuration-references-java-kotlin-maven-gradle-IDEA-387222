package demo;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "demo.injected=${test.only.property}")   // TC-07
class PropertiesAttributeTest {
  @Test
  void contextLoads() {
  }
}
