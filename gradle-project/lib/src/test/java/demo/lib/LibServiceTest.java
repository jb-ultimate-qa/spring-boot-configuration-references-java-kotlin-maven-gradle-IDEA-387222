package demo.lib;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;

class LibServiceTest {
  @Value("${lib.test.only}")                 // TC-09
  String libTestOnly;

  @Value("${test.only.property}")            // XP-02
  String appTestOnly;

  @Test
  void placeholder() {
  }
}
