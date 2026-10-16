package demo.single;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class SingleServiceTest {
  @Value("${my.key}")                        // RL-03
  String myKey;

  @Test
  void runtimeTruth() {
    assertThat(myKey).isEqualTo("test-value");
  }
}
