package demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class ProfiledTest {
  @Value("${my.property}")                   // TC-06
  String myProperty;

  @Test
  void runtimeTruth() {
    assertThat(myProperty).isEqualTo("test-profile");
  }
}
