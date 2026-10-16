package demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class MainServiceTest {
  @Value("${my.property}")                   // TC-04
  String myProperty;

  @Value("${test.only.property}")            // TC-05
  String testOnly;

  @Value("${yaml.test-only}")                // TC-05Y
  String yamlTestOnly;

  @Value("${imported.test.property}")        // TC-14
  String imported;

  @Value("${main.only.property}")            // TC-02T
  String mainOnly;

  @Test
  void runtimeTruth() {
    assertThat(myProperty).isEqualTo("test");
    assertThat(testOnly).isEqualTo("test-only");
    assertThat(yamlTestOnly).isEqualTo("test-yaml-only");
    assertThat(imported).isEqualTo("imported");
    assertThat(mainOnly).isEqualTo("main-only");
  }
}
