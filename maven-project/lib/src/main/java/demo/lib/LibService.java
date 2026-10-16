package demo.lib;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class LibService {
  @Value("${my.property}")                   // TC-08
  String myProperty;

  @Value("${test.only.property:none}")       // NC-04, XP-01 (fold)
  String appTestOnly;

  @Value("${lib.test.only:none}")            // NC-05
  String libTestOnly;
}
